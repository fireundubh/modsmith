from lxml import etree

PRODUCTION = False

XML_PARSER = etree.XMLParser(encoding='utf-8', remove_blank_text=True, strip_cdata=False)

ROW_XPATH = '//*[translate(local-name(), "Row", "row")="row"]'
