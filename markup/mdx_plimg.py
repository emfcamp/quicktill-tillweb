"""markdown extension to enable links to images stored in photologue

"""

import markdown
from photologue.models import Photo
from sorl.thumbnail import get_thumbnail
import os.path
from copy import deepcopy


def _res(f, rs):
    fn, ext = os.path.splitext(f)
    return f"{fn}@{rs}{ext}"


def update_img_tag(t):
    """The image source is a colon-separated string.  The first element
    is the photo name (slug); all remaining elements are keywords.

    """
    src = t.get("src")
    s = src.split(":")
    try:
        photo = Photo.objects.get(slug=s[0])
    except Photo.DoesNotExist:
        return
    imgclass = []
    size = "400x300"
    options = {}
    link = True
    center = False
    for p in s[1:]:
        if p.startswith("size-"):
            size = p[5:]
            if size == "original":
                size = "4000x3000"
                options["upscale"] = False
            elif size == "largepage":
                size = "800"
        elif p.startswith("crop-"):
            options["crop"] = p[5:]
        elif p.startswith("quality-"):
            options["quality"] = int(p[8:])
        elif p == "upscale":
            options["upscale"] = True
        elif p == "no-upscale":
            options["upscale"] = False
        elif p == "padding":
            options["padding"] = True
        elif p == "padding-colour-":
            options["padding_color"] = p[15:]
        elif p == "nolink":
            link = False
        elif p == "center":
            center = True
        else:
            imgclass.append(p)
    im = get_thumbnail(photo.image, size, **options)
    t.set("src", im.url)
    t.set("srcset", f"{im.url}, {_res(im.url, '1.5x')} 1.5x, "
          f"{_res(im.url, '2x')} 2x")
    if imgclass:
        t.set("class", ' '.join(imgclass))
    t.set("width", str(im.width))
    t.set("height", str(im.height))
    if photo.is_public and link:
        # Replace the IMG element with an "A" element linking to the
        # photo page, with the IMG element as a child.
        img = deepcopy(t)
        t.clear()
        t.tag = "a"
        t.set('href', photo.get_absolute_url())
        t.append(img)
    if center:
        # Replace the element with a "DIV" element, with the element
        # as a child
        img = deepcopy(t)
        t.clear()
        t.tag = "div"
        t.set("class", "center")
        t.append(img)


def find_img_tags(element):
    for child in element:
        if child.tag == "img":
            update_img_tag(child)
        find_img_tags(child)


def convert_hr_to_clear(element):
    for child in element:
        if child.tag == "hr":
            child.tag = "p"
            child.set("class", "clearboth")
        convert_hr_to_clear(child)


class PLImgTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        find_img_tags(root)
        convert_hr_to_clear(root)


class PLImgExtension(markdown.Extension):
    def extendMarkdown(self, md):
        tp = PLImgTreeprocessor(md)
        md.treeprocessors.register(tp, 'plimg', 20)
