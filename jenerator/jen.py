import sys, os, shutil, pkgutil, json
from jinja2 import Environment, FileSystemLoader
from django.utils import feedgenerator
from jenerator.processors import process


METASEP = '__'
DATEFMT = '%Y-%m-%d'
IMGEXTS = ['jpg', 'png']
SAFECHARS = 'abcdefghijklmnopqrstuvwxyz0123456789.-_'
ALTCHAR = '-'

STATICDIR = 'static'
PAGESDIR = 'pages'
PICSDIR = 'pictures'
CATSDIR = 'categories'
TMPLSDIR = 'templates'
CONFIGDIR = '.jenerator'
CONFIGFILE = 'config'

PAGETMPL = 'page' + os.extsep + 'html'
CATTMPL = 'category' + os.extsep + 'html'
INDTMPL = 'index' + os.extsep + 'html'
DEFAULTTMPL = 'default' + os.extsep + 'html'

DATEINDEX = -2
TITLEINDEX = -1


def util_strip_chars(s):
    """
    Return a copy of the given string with only safe characters. Unsafe
    characters are converted to a particular alternate character given by
    'ALTCHAR'.
    """
    outstr = s
    for c in s:
        if c not in SAFECHARS:
            outstr = outstr.replace(c, ALTCHAR)
    return outstr


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
    raw_content, html_content = process(os.path.join(path, name))
    raw_date = util_parse_date(name)
    raw_title = util_parse_title(name)
    nice_title = ' '.join(raw_title.split('_'))
    link = util_strip_chars('-'.join(raw_title.lower().split('_')))
    category_names = util_parse_categories(name)
    context = {
            'raw_content': raw_content,
            'html_content': html_content,
            'raw_date': raw_date,
            'raw_title': raw_title,
            'nice_title': nice_title,
            'cat_names': category_names,
            'link': link 
    }
    return context


def parse_category(path, name):
    full_path = os.path.join(path,
            name + os.extsep + 'md')
    if os.path.isfile(full_path):
        raw_content, html_content = process(full_path)
    else:
        raw_content = ''
        html_content = ''
    raw_date = ''
    raw_title = name
    nice_title = ' '.join(raw_title.split('_'))
    link = util_strip_chars('-'.join(raw_title.lower().split('_')))
    context = {
            'raw_content': raw_content,
            'html_content': html_content,
            'raw_date': raw_date,
            'raw_title': raw_title,
            'nice_title': nice_title,
            'link': link 
    }
    return context


def config_set(opts, option, value=''):
    """
    Set a configuration option for a site.
    """
    if 'location' in opts:
        site_path = opts.location
    elif 'site' in opts:
        site_path = opts.site
    else:
        raise Exception('No site specified, cannot set options')
    with open(os.path.join(site_path, CONFIGDIR, CONFIGFILE), 'r') as f:
        config_data = json.load(f)
    config_data[option] = value
    with open(os.path.join(site_path, CONFIGDIR, CONFIGFILE), 'w') as f:
        json.dump(config_data, f)


def config_getall(opts):
    if 'location' in opts:
        site_path = opts.location
    elif 'site' in opts:
        site_path = opts.site
    else:
        raise Exception('No site specified, cannot set options')
    with open(os.path.join(site_path, CONFIGDIR, CONFIGFILE), 'r') as f:
        config_data = json.load(f)
    return config_data


def config_get(opts, option):
    """
    Get the value of a configuration option for a site.
    """
    return config_getall(opts).get(option, '')


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
    # Load files
    tmpl_data = pkgutil.get_data('jenerator',
            'skel/templates_default.html')
    open(os.path.join(base, TMPLSDIR, 'default.html'), 'wb').write(tmpl_data)
    ind_data = pkgutil.get_data('jenerator',
            'skel/index.md')
    open(os.path.join(base, 'index.md'), 'wb').write(ind_data)
    # Create meta directory
    os.makedirs(os.path.join(base, CONFIGDIR))
    with open(os.path.join(base, CONFIGDIR, CONFIGFILE), 'w') as f:
        f.write('{}')
    config_set(opts, 'author_name', opts.author)
    config_set(opts, 'author_email', opts.email)
    config_set(opts, 'site_title', opts.title)


def cmd_config(opts):
    """
    Configure a site.
    """
    if opts.set:
        # Parse option and value
        option, value = opts.set.split('=', 1)
        config_set(opts, option, value)
    elif opts.option:
        value = config_get(opts, opts.option)
        sys.stdout.write('{}={}\n'.format(
                opts.option, value))
    else:
        # TODO: Display all options and values?
        pass


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
        shutil.copytree(os.path.join(opts.site, STATICDIR), opts.target)

    # Copy the pictures directory
    shutil.copytree(os.path.join(opts.site, PICSDIR),
            os.path.join(opts.target, PICSDIR))

    # Create the template environment, pull from template directory
    template_environment = Environment(
            loader=FileSystemLoader(os.path.join(opts.site, TMPLSDIR)))

    # Establish the build queue - stores contexts to be built
    buildq = []

    # Global context is integrated with the context for each page to provide
    # info about other pages and categories that exist in the site
    global_context = {
            'cat_pages': {}, # category -> pages in that category
            'categories': [], # category contexts
            'all_cat_names': set(), # category names as strings
            'all_pages': [] # page contexts
    }
    # Build pages
    for root, dirs, files in os.walk(os.path.join(opts.site, PAGESDIR)):
        for name in files:
            context = parse_page(root, name)
            # Add page image to context
            context['img_path'] = util_image_ext(os.path.join(opts.site,
                    PICSDIR, PAGESDIR, context['raw_title'] + os.extsep))
            # Add template path to context
            tmpl_path = os.path.join(PAGESDIR,
                    context['raw_title'] + os.extsep + 'html')
            if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                    tmpl_path)):
                tmpl_path = PAGETMPL
            if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                    tmpl_path)):
                tmpl_path = DEFAULTTMPL
            if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                    tmpl_path)):
                # TODO: Grab default template from /data instead of failing
                sys.stderr.write('Error: No default template defined\n')
                sys.exit(1)
            context['tmpl_path'] = tmpl_path
            # Add page to global categories
            global_context['all_cat_names'].update(context['cat_names'])
            for c in context['cat_names']:
                global_context['cat_pages'].setdefault(c, []).append(context)
            # Set page type
            context['type'] = 'page'
            # Add page to queue
            buildq.append(context)
            # Add page to global pages list
            global_context['all_pages'].append(context)
    # Build category pages
    for category in global_context['all_cat_names']:
        context = parse_category(os.path.join(opts.site, CATSDIR),
                category)
        # Add category image
        context['img_path'] = util_image_ext(os.path.join(opts.site,
                PICSDIR, CATSDIR, category))
        # Add template
        tmpl_path = os.path.join(CATSDIR,
                context['raw_title'] + os.extsep + 'html')
        if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                tmpl_path)):
            tmpl_path = CATTMPL
        if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                tmpl_path)):
            tmpl_path = DEFAULTTMPL
        if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
                tmpl_path)):
            # TODO: Grab default template from /data instead of failing
            sys.stderr.write('Error: No default template defined\n')
            sys.exit(1)
        context['tmpl_path'] = tmpl_path
        # Set page type
        context['type'] = 'category'
        # Add category page to queue
        buildq.append(context)
        # Add the category context to the global list
        global_context['categories'].append(context)
    # Build index page
    context = parse_category(opts.site, 'index')
    # Add image
    context['img_path'] = util_image_ext(os.path.join(opts.site,
            PICSDIR, 'index'))
    # Add template
    tmpl_path = INDTMPL
    if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
            tmpl_path)):
        tmpl_path = DEFAULTTMPL
    if not os.path.isfile(os.path.join(opts.site, TMPLSDIR,
            tmpl_path)):
        # TODO: Grab default template from /data instead of failing
        sys.stderr.write('Error: No default template defined\n')
        sys.exit(1)
    context['tmpl_path'] = tmpl_path
    # Set page type
    context['type'] = 'index'
    # Add to queue
    buildq.append(context)

    config_context = config_getall(opts)
    for c in buildq:
        final_context = {}
        final_context.update(config_context)
        final_context.update(c)
        final_context.update(global_context)
        template = template_environment.get_template(
                c['tmpl_path'])
        content = template.render(**final_context)
        with open(os.path.join(opts.target,
                c['link'] + os.path.extsep + 'html'), 'w') as f:
            f.write(content)

    # Generate feeds
    site_url = config_get(opts, 'site_url')
    if opts.feeds:
        atom = feedgenerator.Atom1Feed(config_get(opts, 'site_title'),
                config_get(opts, 'site_url'), config_get(opts, 'site_desc'),
                author_email=config_get(opts, 'author_email'),
                author_name=config_get(opts, 'author_name'))
        for page in global_context['all_pages']:
            atom.add_item(page['nice_title'], '{}/{}.html'.format(
                    site_url, page['link']),
                    page['html_content'])
        with open(os.path.join(opts.target, 'index.atom.xml'), 'w') as f:
            f.write(atom.writeString('utf8'))
