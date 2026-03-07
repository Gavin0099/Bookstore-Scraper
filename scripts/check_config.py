import yaml
c = yaml.safe_load(open('config.yaml', encoding='utf-8'))
print('prefix:', c['output']['excel_prefix'])
for x in c['suncolor']['categories']:
    print(f"  {x['name']} -> path={x.get('path')} knd={x['knd']} knd2={x['knd2']}")
