import sys, inspect
import keyword
from xml import dom
from xml.dom.minidom import parse

filename = "C:\\Users\\Dell\\Desktop\\lab\\labtry\\example.xml"
document = None
root = None
context = None

namespace = []
names = []


# ------------------------------------------------------------------------------------------------

def check_name(name: str):
    if keyword.iskeyword(name):
        return False
    return name.isidentifier()


# ------------------------------------------------------------------------------------------------

def get_element(path: str, this_context, tag=None):
    """
    Returns Element if found or None.
    :param path:
    :param this_context:
    :return: DOM Node || None
    """
    mlist = path.split('.')
    local = this_context

    found = False
    for required in mlist:
        found = False
        for child in local.childNodes:
            if isinstance(child, dom.minidom.Element) and child.getAttribute('name') == required:
                if (tag and child.tagName == tag) or not tag:
                    found = True
                    local = child
                    break
        if not found:
            print(f'No {required} element found')
            break

    if not found:
        return None
    return local


def get_up_element(path: str, tag=None):
    """
    Returns found class or None.
    :param path:
    :return: DOM Node || None
    """
    local = context

    while local != root:
        for child in local.childNodes:
            if isinstance(child, dom.minidom.Element) and child.getAttribute('name') == path:
                if (tag and child.tagName == tag) or not tag:
                    return child
        local = local.parentNode
    else:
        for child in local.childNodes:
            if isinstance(child, dom.minidom.Element) and child.getAttribute('name') == path:
                if (tag and child.tagName == tag) or not tag:
                    return child
        local = local.parentNode
    return None


def get_path(this_context):
    res = this_context.getAttribute('name')
    local = this_context
    while local != root:
        local = local.parentNode
        res = local.getAttribute('name') + ('.' if local != root else '') + res
    return res


def add_ref(target, referenced):
    path = get_path(referenced)
    set_ref(target, path)


def set_ref(target, path):
    ref = document.createElement('reference')
    ref.setAttribute('name', path)
    target.appendChild(ref)


# ------------------------------------------------------------------------------------------------

def create_class(classname, parents, metaclass):
    for child in context.childNodes:
        if isinstance(child, dom.minidom.Element) \
                and child.tagName == 'class' and child.getAttribute('name') == classname:
            print('Already exists in current namescope on this level')
            return

    cls = document.createElement('class')
    cls.setAttribute('name', classname)

    if metaclass:
        if metaclass not in names:
            print('No such class! Skipping')
        else:
            cls.setAttribute('metaclass', metaclass)
    if parents:
        for parent in parents:
            first_parent = get_up_element(parent.split('.')[0])
            if parent not in names and first_parent and not get_element(parent, first_parent.parentNode):
                print('No such parent! Skipping')
                continue

            result_parent = get_element(parent, first_parent.parentNode)
            set_ref(result_parent, get_path(context) + ('.' if context != root else '') + f'{classname}')

            pel = document.createElement('parent')
            pel.setAttribute('name', parent)
            cls.appendChild(pel)

    context.appendChild(cls)


def rename_class():
    if context.tagName == 'class':
        cls = input('enter new classname for current class\n')
        if not check_name(cls):
            print('non-valid class name')
            return

        path = get_path(context)

        # 1 - rename ref in parent
        for parent in context.getElementsByTagName('parent'):
            parent_path = parent.getAttribute('name')
            parent_node = get_up_element(parent_path.split('.')[0])
            parent_node = get_element(''.join(parent_path.split('.')[1:]), parent_node)

            ref = None
            for el in parent_node.getElementsByTagName('reference'):
                if el.getAttribute('name') == path:
                    ref = el
                    break

            if not ref:
                print('Oups something went wrong! No ref in parent')
                return

            true_path = path.split('.')
            if len(true_path) == 1:
                true_path = cls
            else:
                true_path.pop()
                true_path.append(cls)
                true_path = '.'.join(true_path)
            ref.setAttribute('name', true_path)
            print(ref.getAttribute('name'))

        # 2 - rename parent in all refs
        for ref in context.getElementsByTagName('reference'):
            ref_path = ref.getAttribute('name')
            ref_node = get_up_element(ref_path.split('.')[0], 'class')

            if len(ref_path.split('.')) > 1:
                ref_node = get_element(''.join(ref_path.split('.')[1:]), ref_node, 'class')

            for parent in ref_node.getElementsByTagName('parent'):
                if parent.getAttribute('name') == path:
                    true_path = path.split('.')
                    if len(true_path) == 1:
                        true_path = cls
                    else:
                        true_path.pop()
                        true_path.append(cls)
                        true_path = '.'.join(true_path)
                    parent.setAttribute('name', true_path)
                    print(parent.getAttribute('name'))

        context.setAttribute('name', cls)
    else:
        print("Context is not class, nothing to rename.")


def delete_class():
    cls = input('enter classname\n')
    for child in context.childNodes:
        if isinstance(child, dom.minidom.Element) and child.tagName == 'class' and \
                child.getAttribute('name') == cls:

            for parent in context.getElementsByTagName('parent'):
                parent_path = parent.getAttribute('name')
                parent_node = get_up_element(parent_path.split('.')[0])
                parent_node = get_element(''.join(parent_path.split('.')[1:]), parent_node)

                ref = None
                for el in parent_node.getElementsByTagName('reference'):
                    if el.getAttribute('name') == path:
                        ref = el
                        break

                if not ref:
                    print('Oups something went wrong! No ref in parent')
                    return

                parent.removeChild(ref)

            context.removeChild(child)
            print('Removed')
            return
    print('None found')


# ------------------------------------------------------------------------------------------------

def create_func(fnc, sign, overriden_class=None):
    for child in context.childNodes:
        if isinstance(child, dom.minidom.Element) and child.tagName == 'function' and \
                child.getAttribute('name') == fnc and child.getAttribute('signature') == sign:
            print('Already exists')
            return

    if context.tagName == 'class':
        if 'self' not in sign.split(',')[0]:
            print('Did you forget or misspelled self parameter?')
            return

    # TO DO: figure out a way to use inspect.Signature
    try:
        exec(f'def {fnc}{sign}: pass')
    except Exception as e:
        print('Error in signature')
        print(e)
        return

    func = document.createElement('function')
    func.setAttribute('name', fnc)
    func.setAttribute('signature', sign)

    if overriden_class and context.tagName == 'class':
        found = False
        if context.getAttribute('name') == overriden_class:
            found = True

        prev = context.getAttribute('name')
        for node in context.getElementsByTagName('parent'):
            if not found and node.getAttribute('name') == overriden_class:
                found = True

            if not found:
                prev = node.getAttribute('name')

            if found:
                parent_path = node.getAttribute('name')
                parent_node = get_up_element(parent_path.split('.')[0], 'class')
                if len(parent_path.split('.')) > 1:
                    parent_node = get_element(''.join(parent_path.split('.')[1:]), parent_node, 'class')

                for func_mem in get_elements_by_tag_name(parent_node, 'function'):
                    if func_mem.getAttribute('name') != fnc and func_mem.getAttribute('signature') != sign:
                        continue

                    ref = document.createElement('reference')
                    ref.setAttribute('name', get_path(context))
                    func_mem.appendChild(ref)
                    break

        if not found:
            print('No class to override')
            return
        func.setAttribute('text', f'mdict = locals()\n'
        f'!del mdict[\'self\']\n'
        f'!del mdict[\'__class__\']\n'
        f'!super({prev}, self).{fnc}(**locals())')

    context.appendChild(func)


def rename_func():
    if context.tagName != 'function':
        return

    cmd = input('enter new name\n')
    if not check_name(cmd):
        print('non-valid name')
        return

    def rename_node(ref_node, name):
        for reference in ref_node.getElementsByTagName('reference'):
            func_path = reference.getAttribute('name')
            func_node = get_up_element(func_path.split('.')[0], 'class')
            if len(func_path.split('.')) > 1:
                func_node = get_element(''.join(func_path.split('.')[1:]), func_node, 'class')

            for func in func_node.getElementsByTagName('function'):
                if func.getAttribute('name') == context.getAttribute('name') and \
                        func.getAttribute('signature') == context.getAttribute('signature'):
                    rename_node(func, name)
                    func.setAttribute('name', cmd)
                    break

    rename_node(context, cmd)

    context.setAttribute('name', cmd)


def del_func(fnc):
    for child in context.childNodes:
        if isinstance(child, dom.minidom.Element) and child.tagName == 'function' and \
                child.getAttribute('name') == fnc:

            if context.tagName != 'class':
                context.removeChild(child)
                return

            path = get_path(context)
            # 1 - remove refs from parents
            for parent in context.getElementsByTagName('parent'):
                parent_path = parent.getAttribute('name')
                parent_node = get_up_element(parent_path.split('.')[0], 'class')
                if len(parent_path.split('.')) > 1:
                    parent_node = get_element(''.join(parent_path.split('.')[1:]), parent_node, 'class')

                ref = None
                for el in parent_node.getElementsByTagName('function'):
                    if el.getAttribute('name') != fnc:
                        continue
                    for func_el in el.getElementsByTagName('reference'):
                        if func_el.getAttribute('name') == path:
                            el.removeChild(func_el)
                            ref = 1
                            break

                if not ref:
                    print('Oups something went wrong! No ref in parent')
                    return

            context.removeChild(child)
            return

    print('Not found')


# ------------------------------------------------------------------------------------------------

def create_attr(attr, val):
    for child in context.childNodes:
        if isinstance(child, dom.minidom.Element) and child.tagName == 'data' and \
                child.getAttribute('name') == attr:
            print('Already exists')
            return

    node = document.createElement('data')
    node.setAttribute('name', attr)
    node.setAttribute('value', val)

    context.appendChild(node)


def rename_attr():
    if context.tagName != 'data':
        return

    cmd = input('enter new name for attribute\n')

    if not check_name(cmd):
        print('invalid name\n')
        return

    for node in context.parentNode.GetElementsByTagName('data'):
        if node.getAttribute('name') == cmd:
            print('invalid name\n')
            return

    context.setAttribute('name', cmd)


def del_attr(attr):
    mlist = context.getElementsByTagName('data')
    for child in mlist:
        if child.getAttribute('name') == attr:
            context.removeChild(mlist[0])
            return
    print('No such attribute')


# ------------------------------------------------------------------------------------------------

def on_create():
    cmd = input('class/func/attr\n')
    if cmd == 'class':
        cls = input('enter classname\n')
        if not check_name(cls):
            print('non valid name')
            return

        parents = input('enter parents\n')
        metaclass = input('enter metaclass\n')

        if parents == '':
            parents = None
        else:
            parents = parents.split(' ')

        if metaclass == '':
            metaclass = None

        # check context for same name
        for child in context.childNodes:
            if child.attributes and child.attributes['name'] == cls:
                print('This class is already in this namescope.')
                return

        create_class(cls, parents, metaclass)
    elif cmd == 'func':
        fnc = input('enter function name\n')
        signature = input('enter signature\n')
        overriden = input('enter override\n')
        create_func(fnc, signature, overriden)
    elif cmd == 'attr':
        name = input('name\n')
        val = input('value\n')
        create_attr(name, val)


def on_rename():
    cmd = input('class/func/attr\n')
    if cmd == 'class':
        rename_class()
    elif cmd == 'func':
        rename_func()
    elif cmd == 'attr':
        rename_attr()


def on_remove():
    cmd = input('class/func/attr\n')
    if cmd == 'class':
        delete_class()
    elif cmd == 'func':
        cmd = input('func name\n')
        del_func(cmd)
    elif cmd == 'attr':
        cmd = input('attr name\n')
        del_attr(cmd)


# ------------------------------------------------------------------------------------------------

def change_context():
    global context
    cmd = input('back or classname or funcname or attrname( function myFunction )\n')
    if cmd == 'back':
        if context.localName != 'data':
            context = context.parentNode
    else:
        children = context.childNodes
        for child in children:
            if isinstance(child, dom.minidom.Element) and child.tagName == cmd.split(' ')[0] \
                    and child.getAttribute('name') == cmd.split(' ')[1]:
                context = child
                print('Context changed')
                break


def import_module():
    cmd = input('module name\n')

    module_obj = __import__(cmd)
    # create a global object containging our module
    globals()[cmd] = module_obj

    for i in inspect.getmembers(module_obj):
        if isinstance(i[1], type):
            namespace.append(i)
            names.append(i[0])


def save():
    with open(filename, 'w') as fstream:
        document.writexml(fstream)
    print('SAVED')


def get_elements_by_tag_name(node, tag):
    res = []
    for el in node.childNodes:
        if isinstance(el, dom.minidom.Element) and el.tagName == tag:
            res.append(el)

    return res


def gen_code():
    def form_indent(num: int):
        return ''.join(['    ' for _ in range(num)])

    lines = []

    with open('test.py', 'w') as fout:

        def generator(node, indent):
            empty = True
            for attr in get_elements_by_tag_name(node, 'data'):
                empty = False
                formed = '\n' + form_indent(indent) + attr.getAttribute('name') + attr.getAttribute('value') + '\n'

                lines.append(formed)
                fout.write(formed)

            for func in get_elements_by_tag_name(node, 'function'):
                empty = False
                txt = (func.getAttribute('text') if func.getAttribute('text') != '' else 'pass')
                if '!' in txt:
                    txt = txt.replace('!', '\n' + form_indent(indent + 1))
                formed = '\n' + form_indent(indent) + 'def ' + func.getAttribute('name') + func.getAttribute(
                    'signature') + \
                         ':' + '\n' + form_indent(indent + 1) + txt + '\n'

                lines.append(formed)
                fout.write(formed)

            for cls in get_elements_by_tag_name(node, 'class'):
                empty = False
                parents = ','.join([el.getAttribute('name') for el in cls.getElementsByTagName('parent')])
                if parents != '':
                    parents = '(' + parents + ')'

                formed = '\n\n' + form_indent(indent) + 'class ' + cls.getAttribute('name') + parents + ':' + '\n'

                lines.append(formed)
                fout.write(formed)

                generator(cls, indent + 1)

            if node.tagName == 'class' and empty:
                formed = form_indent(indent) + 'pass' + '\n'
                lines.append(formed)
                fout.write(formed)

        generator(root, 0)

    print('\n'.join(lines))


# ------------------------------------------------------------------------------------------------

def main():
    exit_flag = False
    while not exit_flag:
        print('context: ', context.getAttribute('name'))
        cmd = input('Enter command(? for help)\n')

        if cmd == 'exit':
            exit_flag = True
        elif cmd == 'save':
            save()
        elif cmd == '?':
            print(
                '? - help\n save - save\n exit - exit\n crt - create\n goto - goto context \n rnm - rename\n '
                'del - delete\n import - import module\n namespace \n names \n gen - generate py module \n'
                'docs - generate documentation')
        elif cmd == 'crt':
            on_create()
        elif cmd == 'rnm':
            on_rename()
        elif cmd == 'del':
            on_remove()
        elif cmd == 'goto':
            change_context()
        elif cmd == 'import':
            import_module()
        elif cmd == 'namespace':
            for i in namespace:
                print(i)
        elif cmd == 'names':
            for i in names:
                print(i)
        elif cmd == 'test':
            module_obj = __import__(cmd)
            print(help(module_obj))
        elif cmd == 'gen':
            gen_code()
        elif cmd == 'docs':
            with open('docs.txt', 'w') as fout:
                sys.stdout = fout
                module_obj = __import__('test')
                help(module_obj)
                sys.stdout = sys.__stdout__
                print('Docs generated')


if __name__ == "__main__":
    document = parse(filename)
    root = document.getElementsByTagName('data')[0]
    context = root
    main()

# clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
# print(clsmembers)
# print(globals())
# print(locals())
# print(vars())
