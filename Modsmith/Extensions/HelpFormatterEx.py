import argparse


class HelpFormatterEx(argparse.HelpFormatter):
    def __init__(self, prog: str, indent_increment: int = 2, max_help_position: int = 35, width: int = 240) -> None:
        """
        Increased max_help_position from 24 (default) to 27 to fit longer argument names
        :param prog: Module name
        :param indent_increment: Indentation for arguments in number of spaces
        :param max_help_position: Max outdent for help text
        :param width: Max width of usage text
        """
        super(HelpFormatterEx, self).__init__(prog, indent_increment, max_help_position, width)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """
        Remove metavars from printing (w/o extra space before comma)
        and support tuple metavars for positional arguments
        """
        _print_metavar = False

        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar = self._metavar_formatter(action, default)(1)
            return ', '.join(metavar)

        parts: list = []

        if action.nargs == 0:
            parts.extend(action.option_strings)
        else:
            default = self._get_default_metavar_for_optional(action)
            args_string = ' {0}'.format(self._format_args(action, default)) if _print_metavar else ''
            for option_string in action.option_strings:
                parts.append(f'{option_string}{args_string}')

        return ', '.join(parts)

    def _get_help_string(self, action: argparse.Action) -> str:
        text: str = str(action.help)

        if not hasattr(action, 'default'):
            return text

        if action.default is None:
            return text

        if action.default == '==SUPPRESS==':
            return text

        default_type = getattr(action, 'type') if hasattr(action, 'type') else None

        if default_type is str:
            text = f'{text} (type: {default_type.__name__}, default: "{action.default}")'
        else:
            if default_type is None:
                default_type = 'bool'
            text = f'{text} (type: {default_type}, default: {action.default})'

        return text
