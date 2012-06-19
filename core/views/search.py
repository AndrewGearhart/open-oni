import datetime, re, json
from rfc3339 import rfc3339

from django.db.models import Q
from django.conf import settings
from django.core import urlresolvers
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template

from chronam.core import index, models
from chronam.core import forms
from chronam.core.decorator import opensearch_clean, cache_page, cors
from chronam.core.utils.utils import _page_range_short

@cors
@cache_page(settings.DEFAULT_TTL_SECONDS)
@opensearch_clean
def search_pages_results(request, view_type='gallery'):
    context = RequestContext(request, {})
    try:
        curr_page = int(request.REQUEST.get('page', 1))
    except ValueError, e:
        curr_page = 1

    page_title = "Search Results"
    # front page only
    try:
        sequence = int(request.REQUEST.get('sequence', '0'))
    except ValueError, e:
        sequence = 0
    # set results per page value
    try:
        rows = int(request.REQUEST.get('rows', '20'))
    except ValueError, e:
        rows = 20
    q = request.GET.copy()
    q['rows'] = rows
    q['sequence'] = sequence
    paginator = index.SolrPaginator(q)
    try:
        page = paginator.page(curr_page)
    except InvalidPage:
        url = urlresolvers.reverse('chronam_search_pages_results')
        # Set the page to the first page
        q['page'] = 1 
        return HttpResponseRedirect('%s?%s' % (url, q.urlencode()))
    start = page.start_index()
    end = page.end_index()
    # figure out the next page number
    query = request.GET.copy()
    if page.has_next():
        query['page'] = curr_page + 1
        next_url = '?' + query.urlencode()
        # and the previous page number
    if page.has_previous():
        query['page'] = curr_page - 1
        previous_url = '?' + query.urlencode()
       
    host = request.get_host()
    format = request.GET.get('format', None)
    if format == 'atom':
        feed_url = 'http://' + host + request.get_full_path()
        updated = rfc3339(datetime.datetime.now())
        return render_to_response('search_pages_results.xml',
                                  dictionary=locals(),
                                  context_instance=RequestContext(request),
                                  mimetype='application/atom+xml')
    elif format == 'json':
        results = {
            'startIndex': start ,
            'endIndex': end,
            'totalItems': paginator.count,
            'itemsPerPage': rows,
            'items': [p.solr_doc for p in page.object_list],
        }
        for i in results['items']:
            i['url'] = 'http://' + request.get_host() + i['id'].rstrip('/') + '.json'
        json_text = json.dumps(results, indent=2)
        # jsonp?
        if request.GET.get('callback') != None:
            json_text = "%s(%s);" % (request.GET.get('callback'), json_text)
        return HttpResponse(json_text, mimetype='application/json')
    page_range_short = list(_page_range_short(paginator, page))
    # copy the current request query without the page and sort
    # query params so we can construct links with it in the template
    q = request.GET.copy()
    q = q.urlencode()
    
    # get an pseudo english version of the query
    english_search = paginator.englishify()
   
    # get some stuff from the query string for use in the form
    lccns = query.getlist('lccn')
    states = query.getlist('state')

    # figure out the sort that's in use
    sort = query.get('sort', 'relevance')
    if view_type == "list":
        template = "search_pages_results_list.html"
    else:        
        template = "search_pages_results.html"
    page_list = []
    for count in range(len(page.object_list)):
        page_list.append((count+start, page.object_list[count]))
    return render_to_response(template, dictionary=locals(),
                              context_instance=RequestContext(request))

@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_titles(request):
    browse_val = [chr(n) for n in range(65, 91)]
    browse_val.extend([str(i) for i in range(10)])
    form = forms.SearchTitlesForm()
    title_count = models.Title.objects.all().count()
    page_name = "directory"
    page_title = "Search U.S. Newspaper Directory, 1690-Present"
    template = "news_directory.html"
    collapse_search_tab = True
    return render_to_response(template, dictionary=locals(),
                              context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_titles_opensearch(request):
    host = request.get_host()
    return render_to_response('search_titles_opensearch.xml',
            mimetype='application/opensearchdescription+xml',
            dictionary=locals(), context_instance=RequestContext(request))


@cache_page(settings.DEFAULT_TTL_SECONDS)
def search_pages_opensearch(request):
    host = request.get_host()
    return render_to_response('search_pages_opensearch.xml',
            mimetype='application/opensearchdescription+xml',
            dictionary=locals(), context_instance=RequestContext(request))

@cors
@cache_page(settings.DEFAULT_TTL_SECONDS)
def suggest_titles(request):
    q = request.GET.get('q', '')
    q = q.lower()

    # remove initial articles (maybe there are more?)
    q = re.sub(r'^(the|a|an) ', '', q)

    # build up the suggestions
    # See http://www.opensearch.org/Specifications/OpenSearch/Extensions/Suggestions/1.0
    # for details on why the json is this way

    titles = []
    descriptions = []
    urls = []
    host = request.get_host()

    lccn_q = Q(lccn__startswith=q)
    title_q = Q(name_normal__startswith=q)
    for t in models.Title.objects.filter(lccn_q | title_q)[0:50]:
        titles.append(unicode(t))
        descriptions.append(t.lccn)
        urls.append("http://" + host + t.url)

    suggestions = [q, titles, descriptions, urls]
    json_text = json.dumps(suggestions, indent=2)
    # jsonp?
    if request.GET.get("callback") != None:
        json_text = "%s(%s);" % (json.GET.get("callback"), json_text)
    return HttpResponse(json_text, mimetype='application/x-suggestions+json')

