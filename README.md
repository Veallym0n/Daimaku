# Daimaku
顾名思义，一个代码的数据库....

> (好吧，用数据库查询的方式审计 python 代码)

###原理特别傻逼
就是把传入的代码进行AST抽象，然后每个ast节点都有个parent节点和自己的随机id
然后把一些关键的ast类型写到一个缓存里，通过pandas导出到sqlite, 结合可以自己创建的udf，就能操作这个ast树了。

###运行方式比较简单。
```
find /somepath -name "*.py" -type f | python daimaku.py [-mode [json|psql|...]] [-sql "select ...."] 
```

###给一个查找可能是SQL注入的例子...
```
select f.func_name,source(parent(s.id)) as code,s.file,s.line from strings s, functions f where lower(s.string) like 'select %' and func(get_child_until_type(parent(s.id),'Mod'))!='' and f.id=func(s.id)

╒════╤════════════════╤════════╤═════════════╤═══════════════════════════════════════════════════════════════════╕
│    │ file           │   line │ vuln_func   │ vuln_source                                                       │
╞════╪════════════════╪════════╪═════════════╪═══════════════════════════════════════════════════════════════════╡
│  0 │ sample/test.py │     12 │ get_data    │ ('select * from sampleTable where username="%s"' % self.whatever) │
╘════╧════════════════╧════════╧═════════════╧═══════════════════════════════════════════════════════════════════╛

```

### 题外话
如果，您觉得这个代码有用的话，请fork,star,watch素质三连....其实我觉得，是个人都能看懂这个玩意儿，也需要你们的udf :)
