import astor
import ast
import re
import md5
from traceback import print_exc as pex

UDFList = {}

def udf(name):
    def wrap(f):
        f.name = name
        UDFList[name] = f
        return f
    return wrap

@udf('cat')
def catFile(item):
    print open(item).read()


@udf('regexp')
def regexp(item, pattern):
    return bool(re.search(pattern,item))

@udf('source')
def toSource(codeid):
    try:
        node = toSource.cls.CodeCache.get(codeid,None)
        if not node: return ''
        return astor.to_source(node)
    except Exception,e:
        pex()
        raise Exception(e)

@udf('parent')
def toParent(codeid):
    try:
        node = toParent.cls.CodeCache.get(codeid,None)
        if not node: return ''
        return node.parent.codeid
    except Exception,e:
        pex()
        raise Exception(e)

@udf('func')
def getTheFunc(codeid):
    node = getTheFunc.cls.CodeCache.get(codeid,None)
    if not node: return ''
    cnode = node
    while not cnode.parent.__class__.__name__ in ('Module','FunctionDef'):
        cnode = cnode.parent
    return cnode.parent.codeid


@udf('get_type_in_parent')
def toParentUntilType(codeid, typ):
    node = toParentUntilType.cls.CodeCache.get(codeid,None)
    if not node: return ''
    cnode = node
    while not cnode.parent.__class__.__name__ == typ:
        cnode = cnode.parent
    return cnode.parent.codeid


@udf('walk_child_by_expr')
def walkChildByExpr(codeid, expr):
    try:
        node = walkChildByExpr.cls.CodeCache.get(codeid,None)
        if not node: return ''
        for subnode in ast.walk(node):
            if eval(expr):
                return subnode.codeid
        return ''
    except:
        pex()
        return ''
        

@udf('walk_child_until_type')
def walkChildByType(codeid, typ):
    try:
        node = walkChildByType.cls.CodeCache.get(codeid,None)
        if not node: return ''
        for subnode in ast.walk(node):
            if subnode.__class__.__name__==typ:
                return subnode.codeid
    except:
        pex()
    return ''

@udf('get_child_by_expr')
def getChildByExpr(codeid, expr):
    node = getChildByExpr.cls.CodeCache.get(codeid,None)
    if not node: return ''
    for subnode in ast.iter_child_nodes(node):
        if eval(expr):
            return subnode.codeid
    return ''

@udf('get_child_until_type')
def getChildByType(codeid, typ):
    node = getChildByType.cls.CodeCache.get(codeid,None)
    if not node: return ''
    for subnode in ast.iter_child_nodes(node):
        if subnode.__class__.__name__==typ:
            return subnode.codeid
    return ''

@udf('has_id')
def hasID(codeid, subcodeid):
    node = hasID.cls.CodeCache.get(codeid,None)
    if not node: return False
    return bool(any(subnode.codeid == subcodeid in ast.walk(node)))

@udf('node_sign')
def nodeSign(codeid):
    node = hasID.cls.CodeCache.get(codeid,None)
    if not node: return ''
    return md5.md5(str([subnode.__class__.__name__ for subnode in ast.walk(node)])).hexdigest()

@udf('file')
def getFile(codeid):
    node = getFile.cls.CodeCache.get(codeid,None)
    if not node: return ''
    return node.file

@udf('lineno')
def getLineno(codeid):
    node = getLineno.cls.CodeCache.get(codeid,None)
    if not node: return ''
    return node.line

def run(cls):
    for udf,udf_func in UDFList.iteritems():
        udf_func.cls = cls
        co_argcount = udf_func.func_code.co_argcount
        cls.codedb.create_function(udf, co_argcount, udf_func)
