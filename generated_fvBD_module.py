#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: generated_fvBD_module
short_description: Manage Bridge Domain (fv:BD)
description:
- 
notes:
- More information about the internal APIC class B(fv:BD) from
  L(the APIC Management Information Model reference,https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Maxwell Lin-He (@maxyso)
version_added: '2.7'
options: 
  OptimizeWanBandwidth:
    description:
    -  
    choices: [ no, yes ] 
  arpFlood:
    description:
    -  
    choices: [ no, yes ] 
  descr:
    description:
    -  
  epClear:
    description:
    -  
    choices: [ no, yes ] 
  epMoveDetectMode:
    description:
    -  
    choices: [ garp ] 
  intersiteBumTrafficAllow:
    description:
    -  
    choices: [ no, yes ] 
  ipLearning:
    description:
    -  
    choices: [ no, yes ] 
  lcOwn:
    description:
    -  
    choices: [ local, policy, replica, resolveOnBehalf, implicit ] 
  llAddr:
    description:
    -  
  mac:
    description:
    -  
  mcastAllow:
    description:
    -  
    choices: [ no, yes ] 
  modTs:
    description:
    -  
    choices: [ never ] 
  name:
    description:
    - [] 
    aliases: [ bridge_domain ] 
  ownerKey:
    description:
    -  
  ownerTag:
    description:
    -  
  pcTag:
    description:
    -  
    choices: [ any ] 
  uid:
    description:
    -  
  unkMacUcastAct:
    description:
    -  
    choices: [ flood, proxy ] 
  unkMcastAct:
    description:
    -  
    choices: [ flood, opt-flood ] 
  vmac:
    description:
    -  
    choices: [ not-applicable ] 
  tenant:
    description:
    - [] 
  state: 
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present 

extends_documentation_fragment: aci
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = aci_argument_spec()
    argument_spec.update({ 
        'OptimizeWanBandwidth': dict(type='str', choices=['no', 'yes'], ),
        'arpFlood': dict(type='str', choices=['no', 'yes'], ),
        'descr': dict(type='str',),
        'epClear': dict(type='str', choices=['no', 'yes'], ),
        'epMoveDetectMode': dict(type='str', choices=['garp'], ),
        'intersiteBumTrafficAllow': dict(type='str', choices=['no', 'yes'], ),
        'ipLearning': dict(type='str', choices=['no', 'yes'], ),
        'lcOwn': dict(type='str', choices=['local', 'policy', 'replica', 'resolveOnBehalf', 'implicit'], ),
        'llAddr': dict(type='str',),
        'mac': dict(type='str',),
        'mcastAllow': dict(type='str', choices=['no', 'yes'], ),
        'modTs': dict(type='str', choices=['never'], ),
        'name': dict(type='str', aliases=['bridge_domain']),
        'ownerKey': dict(type='str',),
        'ownerTag': dict(type='str',),
        'pcTag': dict(type='str', choices=['any'], ),
        'uid': dict(type='str',),
        'unkMacUcastAct': dict(type='str', choices=['flood', 'proxy'], ),
        'unkMcastAct': dict(type='str', choices=['flood', 'opt-flood'], ),
        'vmac': dict(type='str', choices=['not-applicable'], ),
        'tenant': dict(type='str',),
        'state': dict(type='str', default='present', choices=['absent', 'present', 'query']),
    })

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[ 
            ['state', 'absent', ['name', 'tenant', ]], 
            ['state', 'present', ['name', 'tenant', ]],
        ],
    )
    
    OptimizeWanBandwidth = module.params['OptimizeWanBandwidth']
    arpFlood = module.params['arpFlood']
    descr = module.params['descr']
    epClear = module.params['epClear']
    epMoveDetectMode = module.params['epMoveDetectMode']
    intersiteBumTrafficAllow = module.params['intersiteBumTrafficAllow']
    ipLearning = module.params['ipLearning']
    lcOwn = module.params['lcOwn']
    llAddr = module.params['llAddr']
    mac = module.params['mac']
    mcastAllow = module.params['mcastAllow']
    modTs = module.params['modTs']
    name = module.params['name']
    ownerKey = module.params['ownerKey']
    ownerTag = module.params['ownerTag']
    pcTag = module.params['pcTag']
    uid = module.params['uid']
    unkMacUcastAct = module.params['unkMacUcastAct']
    unkMcastAct = module.params['unkMcastAct']
    vmac = module.params['vmac']
    tenant = module.params['tenant']
    state = module.params['state']

    aci = ACIModule(module)
    aci.construct_url(
        root_class={
            'aci_class': 'fvTenant',
            'aci_rn': 'uni/tn-{}.format(tenant),
            'filter_target': 'eq(fvTenant.name, "{}")'.format(tenant),
            'module_object': tenant
        }, 
        subclass_1={
            'aci_class': 'fvBD',
            'aci_rn': 'BD-{}.format(name),
            'filter_target': 'eq(fvBD.name, "{}")'.format(name),
            'module_object': name
        }, 
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvBD',
            class_config={ 
                'OptimizeWanBandwidth': OptimizeWanBandwidth,
                'arpFlood': arpFlood,
                'descr': descr,
                'epClear': epClear,
                'epMoveDetectMode': epMoveDetectMode,
                'intersiteBumTrafficAllow': intersiteBumTrafficAllow,
                'ipLearning': ipLearning,
                'lcOwn': lcOwn,
                'llAddr': llAddr,
                'mac': mac,
                'mcastAllow': mcastAllow,
                'modTs': modTs,
                'name': name,
                'ownerKey': ownerKey,
                'ownerTag': ownerTag,
                'pcTag': pcTag,
                'uid': uid,
                'unkMacUcastAct': unkMacUcastAct,
                'unkMcastAct': unkMcastAct,
                'vmac': vmac,
            },
        )

        aci.get_diff(aci_class='fvBD')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()

if __name__ == "__main__":
    main()