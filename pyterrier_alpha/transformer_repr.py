import inspect

def transformer_repr(self):
    cls = self.__class__
    init = self.__init__
    signature = inspect.signature(init)
    mode = 'pos'
    args = []
    for p in signature.parameters.values():
        if p.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            mode = 'kwd'
        try:
            val = getattr(self, f'_{p.name}')
        except AttributeError:
            val = getattr(self, p.name)
        if val != p.default:
            args.append(f'{p.name}={val!r}' if mode == 'kwd' else repr(val))
        else:
            mode = 'kwd' # skip a paramter, force keyword mode
    return cls.__name__ + '(' + ', '.join(args) + ')'
