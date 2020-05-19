
import json

def splitTag(st):

    d=[]
    o = st
    while o and len(o):
        o = o.split("<")
        d.append(o[0])
        if len(o)>1:
            o=o[1].split("/>")
            print(o)
            d.append(o[0])
            o=o[1]
            print(o)
        else:
            break

    print(d)



a="""123<{"title":"粉丝昵称"}/>ffdsfdsf<{"title":"粉丝昵称"}/>"""

splitTag(a)