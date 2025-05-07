#!/usr/bin/env python3

"""
Pandoc preprocessing filter to convert Obsidian-flavored `.MD` files 
into `.tex` output usable with the cheatsheet styles.

To use, run command:

```shell
pandoc 
  -f markdown+tex_math_dollars
     +header_attributes
     +wikilinks_title_after_pipe
     +lists_without_preceding_blankline
     -auto_identifiers
  --filter=filter.py 
  -o ./out.tex ./in.md
```

-> The `markdown` option is obvious; `+tex_math_dollars` for supporting $MATH$
-> `+header_attributes` to support processing of `{.unnumbered .unlisted}` attribute at end of MD headers
-> `+wikilinks_title_after_pipe` to support wikilink-style `[[URL|title]]` links
-> `+lists_without_preceding_blankline` to better support Obsidian-flavoured 
   MarkDown lists, i.e. ones based purely on indentation
-> `-auto_identifiers` to remove the auto-generated identifiers for Headings/Sections
-> `--filter=filter.py` to invoke this panflute filter
"""

from typing import Callable, TypeVar
import panflute as pf
from functools import partial

# --------------------------------------------------------------------------------- #
#                        Type Definitions, Constants, Utils                         #
# --------------------------------------------------------------------------------- #
type Function[P1, O] = Callable[[P1], O]
type BiFunction[P1, P2, O] = Callable[[P1, P2], O]
type Consumer[P1] = Function[P1, None]
type BiConsumer[P1, P2] = BiFunction[P1, P2, None]

INPUT_FORMAT = "markdown+tex_math_dollars+header_attributes+wikilinks_title_after_pipe+lists_without_preceding_blankline-auto_identifiers"
HEADER_ATTR_UNNUMBERED = "unnumbered"
HEADER_ATTR_UNLISTED = "unlisted"
MATH_FORMAT_INLINE = "InlineMath"

def apply_all[T](*args: list[Consumer[T]]):
    """
    Apply all consumers specified, sequentially.
    """
    def go(x: T):
        for f in args:
            f(x)
    return go

mk_raw_inline: Function[str, pf.RawInline] = lambda text: pf.RawInline(text, 'latex')

def rec_convert_text(text: str, doc: pf.Doc):
    return [e.walk(action, doc=doc) for e in pf.convert_text(text, INPUT_FORMAT)]

# --------------------------------------------------------------------------------- #
#                           Individual Preparation Logic                            #
# --------------------------------------------------------------------------------- #
"""
TODO: add logic here as needed
"""


# --------------------------------------------------------------------------------- #
#                              Individual Action Logic                              #
# --------------------------------------------------------------------------------- #
def force_unnumbered_unlisted_heading(h: pf.Header):
    """
    Make headers unnumbered, which will map them to `\\??section*{..}` family of commands, 
    instead of `\\??section{..}` which it is by default. Do so by inserting an `unnumbered`
    header-attribute to all processed headers.
    Additionally, prevents Pandoc from adding them to TOC by inserting `unlisted` attribute.
    """

    if HEADER_ATTR_UNNUMBERED not in h.classes:
        h.classes.append(HEADER_ATTR_UNNUMBERED)
    if HEADER_ATTR_UNLISTED not in h.classes:
        h.classes.append(HEADER_ATTR_UNLISTED)

def make_inline_math_use_imbox(m: pf.Math) -> pf.Element:
    """
    Make inline-math block content be wrapped in custom command `\\iMbox{..}`, which
    surrounds it with a nice inline box, so that reading it is more clear.
    """
    
    if m.format != MATH_FORMAT_INLINE:
        return m
    
    return mk_raw_inline(f"\\iMbox{{{m.text}}}")

def replace_emph_with_textit(el: pf.Emph):
    return [mk_raw_inline("\\textit{"), *el.content, mk_raw_inline("}")]

def replace_link_with_ul(el: pf.Link, doc: pf.Doc):
    # Grab first 'content' item from link: must be string
    if len(el.content) != 1:
        raise Exception(f"Link {el} has non-singleton content list")   
    if not isinstance(el.content[0], pf.Str):
        raise Exception(f"Link {el} has non-Str content")
    
    # Recursively parse inner-text
    inner_text = el.content[0].text
    parsed_content: list[pf.Element] = rec_convert_text(inner_text, doc)
    
    # The result should be exactly one Para with desired inner content
    if len(parsed_content) != 1:
        raise Exception(f"Link's parsed content {parsed_content} has non-singleton list")   
    if not isinstance(parsed_content[0], pf.Para):
        raise Exception(f"Link's parsed content {parsed_content} has has non-Para content")
    
    return [mk_raw_inline("\\ul{"), *parsed_content[0].content, mk_raw_inline("}")]

def replace_images_with_placeholder(el: pf.Image, doc: pf.Doc):
    return mk_raw_inline(f"\\textcolor{{red}}{{\\textbf{{{el.url}}}}}")

def html_tag_polyfill(el: pf.RawInline):
    """
    Provide polyfill parsing for any relevant HTML tags
    """
    
    if el.format != 'html':
        return el
    
    text = el.text
    
    # Map `<u>..</u>` to `\ul{..}`
    match text:
        case "<u>": return mk_raw_inline("\\ul{")
        case "</u>": return mk_raw_inline("}")
    
    # Map `<font ??>..</font>` to nothing => discard colors
    if "<font" in text.lower() or "font>" in text.lower():
        return []
    
    # We don't want random annoying HTML tags slipping through
    raise Exception(f"Cannot parse element: {el}")
    

# --------------------------------------------------------------------------------- #
#                           Individual Finalization Logic                           #
# --------------------------------------------------------------------------------- #
"""
TODO: add logic here as needed
"""


# --------------------------------------------------------------------------------- #
#                               Filter Lifecycle Code                               #
# --------------------------------------------------------------------------------- #
def prepare(doc):
    pass


def header_actions(h: pf.Header, doc: pf.Doc):
    # apply in-place mutable transformations
    apply_all(force_unnumbered_unlisted_heading)(h)

    # return None -> element unchanged
    # return [] -> delete element
    pass

def math_actions(m: pf.Math, doc: pf.Doc):
    # apply pipelined transformations
    m = make_inline_math_use_imbox(m)

    return m

def raw_inline_actions(el: pf.RawInline, doc: pf.Doc):
    # apply pipelined transformations
    el = html_tag_polyfill(el)

    return el

# return None -> element unchanged
# return [] -> delete element
def action(el, doc):
    # Not sure if this is strictly necessary, but just being careful :)
    if doc is None or not (isinstance(el, pf.Element)
            and isinstance(doc, pf.Doc)
            and (doc.format == 'latex' or doc.format == 'panflute')):
        return el
    
    # Route to the appropriate set of actions
    match el:
        case pf.Header(): return header_actions(el, doc)
        case pf.Math(): return math_actions(el, doc)
        case pf.Emph(): return replace_emph_with_textit(el)
        case pf.Link(): return replace_link_with_ul(el, doc)
        case pf.RawInline(): return raw_inline_actions(el, doc) 
        case pf.Image(): return replace_images_with_placeholder(el, doc)
        
    return el

def finalize(doc):
    pass


def main(doc=None):
    return pf.run_filter(action,
                         prepare=prepare,
                         finalize=finalize,
                         doc=doc)

if __name__ == '__main__':
    main()
