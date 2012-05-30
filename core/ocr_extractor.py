import re

from xml.sax.handler import ContentHandler, feature_namespaces
from xml.sax import make_parser

trailing_punctuation = re.compile('''[^a-zA-Z0-9]+$''')

class OCRHandler(ContentHandler):

    def __init__(self):
        self._page = {} 
        self._line = []
        self._coords = {}
        self._language = 'eng'
        self.width = None
        self.height = None

    def startElement(self, tag, attrs):
        if tag == 'String':
            content = attrs.get("CONTENT")
            coord = {
                'hpos': float(attrs.get('HPOS')) / self.width,
                'vpos': float(attrs.get('VPOS')) / self.height,
                'width': float(attrs.get('WIDTH')) / self.width,
                'height': float(attrs.get('HEIGHT')) / self.height
                    }
            self._line.append(content)

            # solr's WordDelimiterFilterFactory tokenizes based on punctuation
            # which removes it from highlighting, so it's important to remove
            # it here as well or else we'll look up words that don't match
            word = re.sub(trailing_punctuation, '', content)
            if word in self._coords:
                self._coords[word].append(coord)
            else:
                self._coords[word] = [coord]
        elif tag == 'Page':
            assert self.width is None
            assert self.height is None
            self.width = float(attrs.get('WIDTH'))
            self.height = float(attrs.get('HEIGHT'))
        elif tag == 'TextBlock':
            self._language = attrs.get('language', 'eng')

    def endElement(self, tag):
        if tag == 'TextLine':
            l = ' '.join(self._line)
            self._line = []
            if self._language in self._page:
                self._page[self._language].append(l)
            else:
                self._page[self._language] = [l]
            self._line = []
        if tag == 'Page':
            for l in self._page.keys():
                self._page[l] = '\n'.join(self._page[l])
    def text(self):
        return "\n".join(self._page.values())

    def lang_text(self):
        return self._page

    def coords(self):
        return self._coords

def ocr_extractor(ocr_file):
    """
    looks at the ocr xml file on disk, extracts the plain text and 
    word coordinates from them.
    """
    handler = OCRHandler()
    parser = make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(feature_namespaces, 0)
    parser.parse(ocr_file)
 
    return handler.lang_text(), handler.coords()
