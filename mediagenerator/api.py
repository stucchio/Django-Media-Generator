import os.path
from django.conf import settings
from django.utils.importlib import import_module
from hashlib import sha1
from itertools import product
from .settings import ROOT_MEDIA_FILTER, GENERATE_MEDIA, GENERATE_MEDIA_DIR, \
    COPY_MEDIA_FILETYPES
from .utils import _load_backend, _get_media_dirs
import os
import shutil

def generate_file(backend, name, filetype, variation, combination=()):
    print 'Generating %s' % name
    output = list(backend.get_output(variation))
    if len(output) == 0:
        output = ('',)
    assert len(output) == 1, \
        'Media group "%s" would result in multiple output files' % name
    output = output[0]
    hash = sha1()
    hash.update(output)

    combination += (hash.hexdigest(),)
    filename = '%s-%s.%s' % (name, '-'.join(combination), filetype)

    path = os.path.join(GENERATE_MEDIA_DIR, filename)
    parent = os.path.dirname(path)
    if not os.path.exists(parent):
        os.makedirs(parent)
    with open(path, 'w') as fp:
        fp.write(output)

def generate_media():
    if os.path.exists(GENERATE_MEDIA_DIR):
        shutil.rmtree(GENERATE_MEDIA_DIR)

    backend_class = _load_backend(ROOT_MEDIA_FILTER)
    for filetype, outputs in GENERATE_MEDIA.items():
        for name, input in outputs.items():
            backend = backend_class(filetype=filetype, input=input)
            variations = backend._get_variations_with_input()
            if not variations:
                generate_file(backend, name, filetype, {})
            else:
                # Generate media files for all variation combinations
                combinations = product(map(variations.__getitem__, variations.keys()))
                for combination in combinations:
                    variation = dict(zip(variations.keys(), combination))
                    generate_file(backend, name, filetype, variation, combination)

    media_files = {}
    for root in _get_media_dirs():
        collect_copyable_files(media_files, root)

    for name, source in media_files.items():
        dst = os.path.join(GENERATE_MEDIA_DIR, name)
        parent = os.path.dirname(dst)
        if not os.path.exists(parent):
            os.makedirs(parent)
        shutil.copyfile(source, dst)

def collect_copyable_files(media_files, root):
    for root_path, dirs, files in os.walk(root):
        for file in files:
            ext = os.path.splitext(file)[1].lstrip('.')
            if ext in COPY_MEDIA_FILETYPES:
                path = os.path.join(root_path, file)
                media_path = path[len(root)+1:]
                media_files[media_path] = path
