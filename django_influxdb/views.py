from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import renderer_classes
from rest_framework import pagination

from . import exceptions


class InfluxGenericViewSet(ViewSet):
    """Generic read only viewset"""

    paginator = pagination.PageNumberPagination()

    @classmethod
    def _get_sorting_tags(cls):
        return cls.sorting_tags

    def param_check(self):
        missing_query_params = []
        for param in self.required_filter_params:
            if param not in self.request.GET:
                missing_query_params.append(param)
        if missing_query_params:
            missing_query_params = ",".join(missing_query_params)
            msg = f"Missing required query parameters: [{missing_query_params}]"
            raise exceptions.MissingParametersException(msg)

    def dispatch(self, request, *args, **kwargs):
        """Reworked DRF dispatch to include parameter check before calling handler
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)
            self.param_check()
            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(request, *args, **kwargs)
        except exceptions.MissingParametersException as e:
            response = Response(f"{e}", status=400)
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


class ListViewSet(InfluxGenericViewSet):
    additional_filter_params = []
    required_filter_params = []

    def generate_tags(self, request):
        tags = {}
        for param in self.additional_filter_params + self.required_filter_params:
            if param in request.GET:
                value = request.GET[param]
                # Check for multiple values
                if len(value.split(",")) > 0:
                    tags[param] = value.split(",")
                else:
                    tags[param] = value
        return tags

    @renderer_classes(JSONRenderer)
    def list(self, request):
        time_start = request.GET.get("time_start")
        time_stop = request.GET.get("time_stop", "now()")
        aggregate = request.GET.get("aggregate")
        data = self.generate_tags(request)
        try:
            dataset = self.influx_model(data=data).filter(time_start, time_stop, aggregate)
        except exceptions.InvalidTimestamp as e:
            return Response(f"{e}", status=400)
        except exceptions.InfluxApiException as e:
            print(e)
            return Response("Bad request - check required fields for proper formating", status=400)
        page = self.paginator.paginate_queryset(dataset, request, view=self)
        if page is not None:
            return self.paginator.get_paginated_response(page)
        return Response(dataset)
