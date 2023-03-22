def parse_prefix(content, prefixs, image_prefixs):
    prefix, match_prefix = _check_prefix(content, prefixs)
    if not match_prefix:
        return "", False, "", False, content
    if len(prefix) > 0:
        str_list = content.split(prefix, 1)
        if len(str_list) == 2:
            content = str_list[1].strip()

    image_prefix, match_image_prefix = _check_prefix(content, image_prefixs)
    if len(image_prefix) > 0:
        str_list = content.split(image_prefix, 1)
        if len(str_list) == 2:
            content = str_list[1].strip()
    return prefix, match_prefix, image_prefix, match_image_prefix, content


def _check_prefix(content, prefix_list):
    if not prefix_list:
        return "", False
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix, True
    return "", False


def _check_contain(content, keyword_list):
    if not keyword_list:
        return False
    for ky in keyword_list:
        if content.find(ky) != -1:
            return ky, True
    return "", False
