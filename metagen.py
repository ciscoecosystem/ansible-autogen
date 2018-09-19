#!/usr/bin/env python

from __future__ import print_function
from insieme.pymit.pyaccess import PyClassDirectory
import json
import multiprocessing
import re

dir = PyClassDirectory()


def getPaciClassName(classMeta):
    return classMeta.getPkgName() + classMeta.getClassName()


def getRnPrefix(classMeta):
    rnFormat = classMeta.getRnFormat()
    dashAt = rnFormat.find('-')
    rnPrefix = rnFormat if dashAt == -1 else rnFormat[:dashAt]
    return rnPrefix


def generateClassMeta(className):
    classMeta = dir.lookup(className)
    paciClassName = classMeta.getPkgName() + classMeta.getClassName()
    paciClassMeta = {}

    paciClassMeta['label'] = classMeta.getLabel()

    paciClassMeta['isAbstract'] = not classMeta.isConcrete()
    paciClassMeta['isConfigurable'] = classMeta.isConfigurable()
    paciClassMeta['isDeletable'] = classMeta.isDeletable()
    paciClassMeta['help'] = classMeta.getHelp()
    #paciClassMeta['name'] = classMeta.getPkgName() + ":" + classMeta.getClassName()
    paciClassMeta['isRelation'] = classMeta.isRelation()
    paciClassMeta['identifiedBy'] = (
        [x for x in classMeta.getOrderedNamingProps()]
    )
    paciClassMeta['rnFormat'] = re.sub(r'(%\((\w+)\)s)',
                                       r'{\2}',
                                       classMeta.getRnFormat())
#    paciClassMeta['properties'] = {
#        p.getName(): {
#            'isConfigurable': p.isConfig(),
#            'help': p._getHelp(),
#            # 'options': p.getType().getLabelConstMap()
#            # use p.getType().getConstants() for both str label and internal value
#            'options': p.getType()._constMap.keys() if p.isConfig() else []
#        }
#        for p in classMeta.getProperties()
#    }
    paciClassMeta['contains'] = []
    for x in classMeta.getContainedClasses():
        paciClassMeta['contains'].append(getPaciClassName(x))
    
    paciClassMeta['containers'] = []
    for x in classMeta.getContainerClasses():
        paciClassMeta['containers'].append(getPaciClassName(x))
    

#    paciClassMeta['rnMap'] = {}
#    for meta in classMeta.getContainedClasses():
#        numNamingProps = 0
#        for _ in meta.getOrderedNamingProps():
#            numNamingProps += 1
#        rnPrefix = getRnPrefix(meta)
#        # ngen allows two contained classes to have the same RN prefix
#        # as long as one has no naming property, and other has naming
#        # property(ies).
#        if numNamingProps > 0:
#            rnPrefix += '-'
#        t = getPaciClassName(meta)
#        if rnPrefix in paciClassMeta['rnMap']:
#            print('Warning: {} is a duplicate RN prefix for {} under {}'
#                  ', other one is {}'.format(
#                      rnPrefix, t, paciClassName,
#                      paciClassMeta['rnMap'][rnPrefix]))
#        else:
#            paciClassMeta['rnMap'][rnPrefix] = t

            
    paciClassMeta["relationTo"] = []
    paciClassMeta["relationFrom"] = []
    #ONE_TO_ONE, ONE_TO_M, N_TO_ONE, N_TO_M = range(4)
    for meta in classMeta.getContainedClasses():
        ### Check if contained class is a relationship class
        if meta.isRelation():
            temppaciClassMeta = {}
            ### is a source relation class
            if hasattr(meta,'_type'):
                temppaciClassMeta["cardinality"] = meta._type
                temppaciClassMeta["class"] = meta.getTargetClassName().replace('.','')
                paciClassMeta["relationTo"].append(temppaciClassMeta)
            else: ### is target relation class 
                temppaciClassMeta["cardinality"] = -1
                temppaciClassMeta["class"] = meta.getSourceClassName().replace('.','')
                paciClassMeta["relationFrom"].append(temppaciClassMeta)

    return (paciClassName, paciClassMeta)

def main():
    classNames = dir.getClassNames()

    aciMeta = {}

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    aciClassMetas = pool.imap(generateClassMeta, classNames)
    aciMeta['classes'] = dict(aciClassMetas)

    with open('aci-meta.json', 'w') as out:
        json.dump(aciMeta, out,
                  sort_keys=True, indent=2, separators=(',', ': '))

if __name__ == '__main__':
    main()
