from lxml import etree

XML_PARSER = etree.XMLParser(encoding='utf-8', remove_blank_text=True, strip_cdata=False)

PRECOMPILED_XPATH_CELL = etree.XPath('Cell/text()')

PRECOMPILED_XPATH_ROW = etree.XPath('//*[translate(local-name(), "Row", "row")="row"]')

PRECOMPILED_XPATH_ROWS = etree.XPath('//*[translate(local-name(), "Rows", "rows")="rows"]')
