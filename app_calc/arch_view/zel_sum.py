import pandas as pd

in_list = [{'property_id__property_name': 'Газон/травяной покров', 'event': 'сохранение', 'total_square': 30.0},
{'property_id__property_name': 'Газон/травяной покров', 'event': 'уничтожение', 'total_square': 23.0},
{'property_id__property_name': 'Газон/травяной покров', 'event': 'устройство', 'total_square': 15.0},
{'property_id__property_name': 'Цветники', 'event': 'восстановление', 'total_square': 3.0},
 {'property_id__property_name': 'Цветники', 'event': 'сохранение', 'total_square': 1.0},
 {'property_id__property_name': 'Цветники', 'event': 'уничтожение', 'total_square': 12.0},
           {'property_id__property_name': 'Цветники', 'event': 'устройство', 'total_square': 46.0},
           {'property_id__property_name': 'Вода', 'event': 'устройство', 'total_square': 46.0},
           {'property_id__property_name': 'Вода', 'event': 'сохранение', 'total_square': 46.0},
           ]

# print(in_list)

df_destroy = pd.DataFrame(in_list)
df_destroy['marker'] = 0
df_destroy.loc[df_destroy.event =='уничтожение', 'marker'] = 1
df_destroy_mark = df_destroy.loc[df_destroy.marker == 1]
df_destroy_mark

df = pd.merge(df_destroy[['property_id__property_name','event','total_square']], df_destroy_mark[['property_id__property_name', 'marker']], how='left', left_on=['property_id__property_name'], right_on=['property_id__property_name'])
df

# df = pd.DataFrame(in_list)
# print(df)

# print(df['property_id__property_name'].unique()[0]     )
#
# for i in in_list:
#     print(i)


# df = pd.DataFrame(in_list)
df_res = (df.loc[df['event']
                        .isin(['сохранение', 'устройство', 'восстановление'])]
                        .groupby('property_id__property_name')
                        .agg({'total_square': 'sum', 'marker':'sum'}))


print('df_res')
print(df_res)
# df_destroy = pd.DataFrame(in_list)
# df_destroy['marker'] = 0
# df_destroy.loc[df_destroy.event =='уничтожение', 'marker'] = 1
# df_destroy_mark = df_destroy.loc[df_destroy.marker == 1]
# df_destroy_mark



dict_exit = df_res.to_dict().get('total_square')
print(f'{dict_exit=}')


dict_exit['mark'] = '1'


print(f'{dict_exit=}')

# df_destroy = pd.DataFrame(in_list)
# output = df_destroy.groupby('property_id__property_name')['event'].apply(
#     lambda x: 1 if 'уничтожение' in x.values else 0
# ).reset_index().rename(columns={'event': 'marker_destroy'}).to_dict('records')
#
# # dict_exit_marcer_destroy = df_res.to_dict().get('total_square')
# new_dict = {}
# for i in output:
#     new_dict[i.get('property_id__property_name')] = i.get('marker_destroy')
# print(new_dict)
#

