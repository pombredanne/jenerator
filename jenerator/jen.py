import sys, os, shutil
from jinja2 import Environment, FileSystemLoader
from markdown import markdown


METASEP = '__'
DATEFMT = '%Y-%m-%d'
IMGEXTS = ['jpg', 'png']

STATICDIR = 'static'
PAGESDIR = 'pages'
PICSDIR = 'pictures'
CATSDIR = 'categories'
TMPLSDIR = 'templates'
PAGETMPL = 'page' + os.extsep + 'html'
CATTMPL = 'category' + os.extsep + 'html'
INDTMPL = 'index' + os.extsep + 'html'

DATEINDEX = -2
TITLEINDEX = -1


def util_parse_categories(name):
    """
    Parse a list of categories from a file name.
    """
    chunks = name.split(METASEP)
    return chunks[:DATEINDEX] if len(chunks) > 2 else []


def util_parse_date(name):
    """
    Parse the date from a file name.
    """
    return name.split(METASEP)[DATEINDEX]


def util_parse_title(name):
    """
    Parse the document title from a file name. Does not insert spaces or
    anything fancy like that.
    """
    return os.path.splitext(name.split(METASEP)[TITLEINDEX])[0]


def util_image_ext(basename):
    for ext in IMGEXTS:
        full = basename + os.extsep + ext
        if os.path.isfile(full):
            return full
    return ''


def parse_page(path, name):
    with open(os.path.join(path, name), 'r') as f:
        raw_content = ''.join(f.readlines())
    html_content = markdown(raw_content)
    raw_date = util_parse_date(name)
    raw_title = util_parse_title(name)
    nice_title = ' '.join(raw_title.split('_'))
    category_names = util_parse_categories(name)
    context = {
            'raw_content': raw_content,
            'html_content': html_content,
            'raw_date': raw_date,
            'raw_title': raw_title,
            'nice_title': nice_title,
            'cat_names': category_names
    }
    return context


def parse_category(path, name):
    full_path = os.path.join(path,
            name + os.extsep + 'md')
    if os.path.isfile(full_path):
        with open(full_path, 'r') as f:
            raw_content = ''.join(f.readlines())
    else:
        raw_content = ''
    html_content = markdown(raw_content)
    raw_date = ''
    raw_title = name
    nice_title = ' '.join(raw_title.split('_'))
    context = {
            'raw_content': raw_content,
            'html_content': html_content,
            'raw_date': raw_date,
            'raw_title': raw_title,
            'nice_title': nice_title,
    }
    return context


def cmd_init(opts):
    """
    Set up a proper directory structure.

    :param opts: Configuration options
    :type opts: NamedTuple-like object
    """
    base = opts.location
    os.makedirs(os.path.join(base, STATICDIR))
    os.makedirs(os.path.join(base, PAGESDIR))
    os.makedirs(os.path.join(base, CATSDIR))
    os.makedirs(os.path.join(base, TMPLSDIR))
    os.makedirs(os.path.join(base, TMPLSDIR, PAGESDIR))
    os.makedirs(os.path.join(base, TMPLSDIR, CATSDIR))
    os.makedirs(os.path.join(base, PICSDIR))
    os.makedirs(os.path.join(base, PICSDIR, PAGESDIR))
    os.makedirs(os.path.join(base, PICSDIR, CATSDIR))
    open(os.path.join(base, 'index.md'), 'w').write('# Index')


def cmd_build(opts):
    """
    Build a site.

    :param opts: Configuration options
    :type opts: NamedTuple-like object
    """
    # Copy static files. We delete the build target directory first, then copy
    # static to it with the new name.
    if os.path.isdir(opts.target):
        if not opts.overwrite:
            sys.stderr.write('Error: target exists, --overwrite to delete\n')
            sys.exit(1)
        else:
            shutil.rmtree(opts.target)

    if opts.nostatic:
        os.makedirs(opts.target)
    else:
        shutil.copytree(os.path.join(opts.source, STATICDIR), opts.target)

    # Copy the pictures directory
    shutil.copytree(os.path.join(opts.source, PICSDIR),
            os.path.join(opts.target, PICSDIR))

    # Create the template environment, pull from template directory
    template_environment = Environment(
            loader=FileSystemLoader(os.path.join(opts.source, TMPLSDIR)))

    # Establish the build queue - elements are (type, context)
    buildq = []

    global_context = {
            'cat_pages': {},
            'categories': [],
            'all_cat_names': set()
    }
    # Build pages
    for root, dirs, files in os.walk(os.path.join(opts.source, PAGESDIR)):
        for name in files:
            context = parse_page(root, name)
            # Add page image to context
            context['img_path'] = util_image_ext(os.path.join(opts.source,
                    PICSDIR, PAGESDIR, context['raw_title'] + os.extsep))
            # Add template path to context
            tmpl_path = os.path.join(PAGESDIR,
                    context['raw_title'] + os.extsep + 'html')
            if not os.path.isfile(os.path.join(opts.source, TMPLSDIR,
                    tmpl_path)):
                tmpl_path = PAGETMPL
            context['tmpl_path'] = tmpl_path
            # Add page to global categories
            global_context['all_cat_names'].update(context['cat_names'])
            for c in context['cat_names']:
                global_context['cat_pages'].setdefault(c, []).append(context)
            # Add page to queue
            buildq.append(('page', context))
    # Build category pages
    for category in global_context['all_cat_names']:
        context = parse_category(os.path.join(opts.source, CATSDIR),
                category)
        # Add category image
        context['img_path'] = util_image_ext(os.path.join(opts.source,
                PICSDIR, CATSDIR, category))
        # Add template
        tmpl_path = os.path.join(CATSDIR,
                context['raw_title'] + os.extsep + 'html')
        if not os.path.isfile(os.path.join(opts.source, TMPLSDIR,
                tmpl_path)):
            tmpl_path = CATTMPL
        context['tmpl_path'] = tmpl_path
        # Add category page to queue
        buildq.append(('category', context))
        # Add the category context to the global list
        global_context['categories'].append(context)
    # Build index page
    context = parse_category(opts.source, 'index')
    # Add image
    context['img_path'] = util_image_ext(os.path.join(opts.source,
            PICSDIR, 'index'))
    # Add template
    context['tmpl_path'] = INDTMPL
    # Add to queue
    buildq.append(('index', context))


    for t, c in buildq:
        final_context = {}
        final_context.update(c)
        final_context.update(global_context)
        template = template_environment.get_template(
                c['tmpl_path'])
        content = template.render(**final_context)
        with open(os.path.join(opts.target,
                c['raw_title'].lower() + os.path.extsep + 'html'), 'w') as f:
            f.write(content)
