from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
import uvicorn
import math


templates = Jinja2Templates(directory='templates')

app = Starlette(debug=True)
app.mount('/static', StaticFiles(directory='statics'), name='static')


@app.route('/')
async def homepage(request):
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context)


class User:
    def __init__(self, pk, first, last, handle):
        self.pk = pk
        self.first = first
        self.last = last
        self.handle = handle


class QuerySet:
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return iter(self.items)

    def offset(self, index):
        return QuerySet(self.items[index:])

    def limit(self, count):
        return QuerySet(self.items[:count])

    def filter(self, **kwargs):
        def filter_condition(item):
            nonlocal kwargs

            for key, value in kwargs.items():
                if value in getattr(item, key).lower():
                    return True
            return False

        return QuerySet([item for item in self.items if filter_condition(item)])

    def order(self, by):
        reverse = False
        if by.startswith('-'):
            reverse = True
            by = by.lstrip('-')

        def sort_key(item):
            nonlocal by
            return (getattr(item, by), item.pk)

        return QuerySet(sorted(self.items, key=sort_key, reverse=reverse))

    def count(self):
        return len(self.items)


def page_range(st, en, cutoff):
    """
    Return an inclusive range from 'st' to 'en',
    bounded within a minimum of 1 and a maximum of 'cutoff'.
    """
    st = max(st, 1)
    en = min(en, cutoff)
    return list(range(st, en + 1))


class ColumnControl:
    def __init__(self, text, url=None, is_sorted=False, is_reverse=False):
        self.text = text
        self.url = url
        self.is_sorted =  is_sorted
        self.is_reverse = is_reverse


class PaginationControl:
    def __init__(self, text, url=None, is_active=False, is_disabled=False):
        self.text = text
        self.url = url
        self.is_active = is_active
        self.is_disabled = is_disabled


@app.route('/tomchristie/blue-river-1234/')
class Homepage(HTTPEndpoint):
    PAGE_SIZE = 5
    SEARCH_FIELDS = ('first', 'last', 'handle')

    async def get(self, request):
        queryset = self.get_queryset()

        search_term = self.get_search_term(request)
        current_page = self.get_page_number(request)
        order_column, reverse_order = self.get_ordering(request)

        queryset = self.search(search_term=search_term, queryset=queryset)
        queryset = self.order(request=request, queryset=queryset)

        # Pagination
        total_items = queryset.count()
        total_pages = max(math.ceil(total_items / self.PAGE_SIZE), 1)
        current_page = max(min(current_page, total_pages), 1)
        page_controls = self.get_page_controls(request, current_page, total_pages)
        queryset = self.paginate(current_page=current_page, queryset=queryset)

        # Columns & Ordering
        column_controls = self.get_column_controls(request, order_column, reverse_order)

        # Render page
        template = "table.html"
        context = {
            "request": request,
            "queryset": queryset,
            "search_term": search_term,
            "column_controls": column_controls,
            "page_controls": page_controls
        }
        return templates.TemplateResponse(template, context)

    def get_search_term(self, request):
        return request.query_params.get('search', default='')

    def get_ordering(self, request):
        ordering = request.query_params.get('order', default='')
        reverse_order = ordering.startswith('-')
        order_column = ordering.lstrip('-')
        if order_column not in ('first', 'last', 'handle'):
            return None, False
        return order_column, reverse_order

    def get_page_number(self, request):
        try:
            return int(request.query_params.get('page', default='1'))
        except (TypeError, ValueError):
            return None

    def get_column_controls(self, request, order_column, reverse_order):
        columns = {"first": "First", "last": "Last", "handle": "Handle"}
        controls = [
            ColumnControl(text="#")
        ]
        for column_name, column_text in columns.items():
            if order_column == column_name:
                is_sorted = True
                is_reverse = reverse_order
                if reverse_order:
                    url = request.url.remove_query_params('order')
                else:
                    url = request.url.include_query_params(order='-' + column_name)
            else:
                url = request.url.include_query_params(order=column_name)
                is_sorted = False
                is_reverse = False
            control = ColumnControl(text=column_text, url=url, is_sorted=is_sorted, is_reverse=is_reverse)
            controls.append(control)
        return controls

    def get_page_controls(self, request, current_page, total_pages):
        if total_pages == 1:
            return []

        # We always have 5 contextual page numbers around the current page.
        if current_page <= 2:
            main_block = page_range(1, 5, cutoff=total_pages)
        elif current_page >= total_pages - 1:
            main_block = page_range(total_pages - 4, total_pages, cutoff=total_pages)
        else:
            main_block = page_range(current_page - 2, current_page + 2, cutoff=total_pages)

        # We always have 2 contextual page numbers at the start.
        start_block = page_range(1, 2, cutoff=total_pages)
        if main_block[0] == 4:
            # If we've only got a gap of one between the start and main blocks
            # then fill in the gap with a page marker.
            # | 1 2 3 4 5 [6] 7 8
            start_block += [3]
        elif main_block[0] > 4:
            # If we've got a gap of more that one between the start and main
            # blocks then fill in the gap with an ellipsis marker.
            # | 1 2 … 5 6 [7] 8 9
            start_block += [None]

        # We always have 2 contextual page numbers at the end.
        end_block = page_range(total_pages - 1, total_pages, cutoff=total_pages)
        if main_block[-1] == total_pages - 3:
            # If we've got a gap of one between the end and main blocks then
            # fill in the gap with an page marker.
            # 92 93 [94] 95 96 97 98 99 |
            end_block = [total_pages - 2] + end_block
        elif main_block[-1] < total_pages - 3:
            # If we've got a gap of more that one between the end and main
            # blocks then fill in the gap with an ellipsis marker.
            # 91 92 [93] 94 95 … 98 99 |
            end_block = [None] + end_block

        seen_numbers = set()
        controls = []

        if current_page == 1:
            previous_url = None
            previous_disabled = True
        elif current_page == 2:
            previous_url = request.url.remove_query_params('page')
            previous_disabled = False
        else:
            previous_url = request.url.include_query_params(page=current_page-1)
            previous_disabled = False

        previous = PaginationControl(
            text="Previous",
            url=previous_url,
            is_disabled=previous_disabled
        )
        controls.append(previous)

        for page_number in start_block + main_block + end_block:
            if page_number is None:
                gap = PaginationControl(
                    text="…",
                    is_disabled=True
                )
                controls.append(gap)
            elif page_number not in seen_numbers:
                seen_numbers.add(page_number)
                if page_number == 1:
                    page_url = request.url.remove_query_params('page')
                else:
                    page_url = request.url.include_query_params(page=page_number)
                page = PaginationControl(
                    text=str(page_number),
                    url=page_url,
                    is_active=page_number == current_page
                )
                controls.append(page)

        if current_page == total_pages:
            next_url = None
            next_disabled = True
        else:
            next_url = request.url.include_query_params(page=current_page+1)
            next_disabled = False

        next = PaginationControl(
            text="Next",
            url=next_url,
            is_disabled=next_disabled
        )
        controls.append(next)
        return controls

    def search(self, search_term, queryset):
        if search_term:
            kwargs = {k: search_term for k in self.SEARCH_FIELDS}
            queryset = queryset.filter(**kwargs)
        return queryset

    def paginate(self, current_page, queryset):
        if current_page is not None and current_page > 1:
            queryset = queryset.offset((current_page - 1) * self.PAGE_SIZE)
        queryset = queryset.limit(self.PAGE_SIZE)
        return queryset

    def order(self, request, queryset):
        order = request.query_params.get('order')
        if order is not None:
            queryset = queryset.order(by=order)
        return queryset

    def get_queryset(self):
        return QuerySet([
            User(pk=1, first='Mark', last='Otto', handle='@mdo'),
            User(pk=2, first='Jacob', last='Thornton', handle='@fat'),
            User(pk=3, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=4, first='Cecilia', last='Rush', handle='@cecilia'),
            User(pk=5, first='Emily', last='Cruise', handle='@ecruise'),
            User(pk=6, first='Tom', last='Foolery', handle='@tom'),
            User(pk=7, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=8, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=9, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=10, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=11, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=12, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=13, first='Larry', last='the Bird', handle='@twitter'),
            User(pk=14, first='Larry', last='the Bird', handle='@twitter'),
        ])


@app.route('/error')
async def error(request):
    """
    An example error. Switch the `debug` setting to see either tracebacks or 500 pages.
    """
    raise RuntimeError("Oh no")


@app.exception_handler(404)
async def not_found(request, exc):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


@app.exception_handler(500)
async def server_error(request, exc):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000, debug=True)
