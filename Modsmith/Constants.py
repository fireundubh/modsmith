from lxml import etree

SHARED_PARSER_OPTIONS = {
    'encoding'         : 'utf-8',
    'remove_blank_text': True,
    'strip_cdata'      : True
}

XML_PARSER \
    = etree.XMLParser(**SHARED_PARSER_OPTIONS, remove_comments=True)

XML_PARSER_ALLOW_COMMENTS \
    = etree.XMLParser(**SHARED_PARSER_OPTIONS, remove_comments=False)

PRECOMPILED_XPATH_CELL \
    = etree.XPath('Cell/text()')

PRECOMPILED_XPATH_ROW \
    = etree.XPath('//*[translate(local-name(), "Row", "row")="row"]')

PRECOMPILED_XPATH_ROWS \
    = etree.XPath('//*[translate(local-name(), "Rows", "rows")="rows"]')
