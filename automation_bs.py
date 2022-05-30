# -*- coding: utf-8 -*-
"""
Created on Thu May 12 21:55:45 2022

@author: naman
"""

import pandas as pd
import numpy as np
import os

os.chdir('C:/Users/naman/Downloads')

def read_file(year,sheet_name):
    
    df = pd.read_excel('FINAL BS 31.03.'+ str(year) + '.xls',sheet_name = sheet_name)
    return df

def clean(df,year):
    
    df = df.replace(' ',np.nan)
    df = df.dropna(axis = 1, how = 'all')
    df = df.iloc[3:]
    df = df.iloc[:,0:4].reset_index(drop = True)
    
    df.columns = ['Particulars','Note No','As at 31.03.'+ str(year),'As at 31.03.'+ str(year-1)]
    df = df.replace(' ',np.nan).replace('PARTICULARS',np.nan)
    df = df[df['As at 31.03.'+ str(year)] != 'AMOUNT (`)']
    df = df[df['As at 31.03.'+ str(year)] != '31.03.'+ str(year)]
    df.dropna(axis = 0, how = 'all', inplace = True)
    df = df.reset_index(drop = True)
    df = df[~(df['Particulars'].isin(['(CIN NO : )','(INDIA) PRIVATE LIMITED']))]
    return df

def clean_groupings(grouping_df,year):
    
    grouping_df = grouping_df.iloc[2:]
    grouping_df = grouping_df[~(grouping_df['Particulars'].str.contains('GROUPING TO THE FINANCIAL STATEMENT AS AT').fillna(False))]
    grouping_df.loc[grouping_df['As at 31.03.'+str(year)].notna(),'As at 31.03.'+str(year-1)] = grouping_df['As at 31.03.'+str(year-1)].fillna(0)
    grouping_df.loc[grouping_df['As at 31.03.'+str(year-1)].notna(),'As at 31.03.'+str(year)] = grouping_df['As at 31.03.'+str(year)].fillna(0)
    grouping_df['groups'] = grouping_df['As at 31.03.'+str(year-1)].isnull().astype(int).cumsum()
    grouping_df.loc[grouping_df['As at 31.03.'+str(year-1)].notnull(),'groups'] = np.nan
    grouping_df['group_no'] = grouping_df['groups']
    grouping_df.loc[grouping_df['groups'].notnull(),'groups'] = grouping_df['Particulars']
    grouping_df['groups'] = grouping_df['groups'].ffill(axis = 0)
    grouping_df['group_no'] = grouping_df['group_no'].ffill(axis = 0)
    
    null_row = pd.DataFrame([[np.nan]*len(grouping_df.columns)],columns = grouping_df.columns)    
    grouping_df = grouping_df.append(null_row)

    grouping_df.loc[(grouping_df['As at 31.03.'+str(year)].isnull()) &
                    (grouping_df['As at 31.03.'+str(year-1)].isnull()),'temp_total'] = 'TOTAL'
    
    # grouping_df['temp_total'] = grouping_df['temp_total'].shift(-1)
    # grouping_df['Note No'] = grouping_df['Note No'].combine_first(grouping_df['temp_total'])
    # grouping_df = grouping_df.drop(['temp_total'],axis = 1)
    
    # x = grouping_df[['groups','group_no']].drop_duplicates().dropna().reset_index(drop = True)
    
    # for i in range(0,len(x)):
    #     x_g = x[x.index == i]['groups'].values[0]
    #     if len(x[x.groups == x_g]) > 1:
    #         x.loc[x.groups == x_g,'cumsum'] = x[x.groups == x_g].groupby('groups').cumcount() + 1
    #     else:
    #         x.loc[x.groups == x_g,'cumsum'] = 1
            
    # x['groups_temp'] = x['groups'] + x['cumsum'].astype(int).astype(str)
    # x = x[['group_no','groups_temp']]
    
    # grouping_df = grouping_df.merge(x)

    return grouping_df

def clean_cfs(df,year):
    
    df = df.replace(' ',np.nan)
    df = df.dropna(axis = 1, how = 'all')
    df = df.iloc[3:]
    df = df.iloc[:,0:5].reset_index(drop = True)
    
    df.columns = ['Serial','Particulars','Note No','As at 31.03.'+ str(year),'As at 31.03.'+ str(year-1)]
    df = df.replace(' ',np.nan).replace('PARTICULARS',np.nan)
    df = df[df['As at 31.03.'+ str(year)] != 'AMOUNT (`)']
    df = df[df['As at 31.03.'+ str(year)] != '31.03.'+ str(year)]
    df.dropna(axis = 0, how = 'all', inplace = True)
    df = df.reset_index(drop = True)
    
    return df

# =============================================================================
# Part 1 - Groupings
# =============================================================================

#Clean Groupings
def merge_groups(year1,year2,sheet_name):
    grouping_2020 = clean(read_file(year1,sheet_name),year1)
    grouping_2021 = clean(read_file(year2,sheet_name),year2)
    grouping_2020 = clean_groupings(grouping_2020,year1).reset_index(drop = True)
    grouping_2021 = clean_groupings(grouping_2021,year2).reset_index(drop = True)
    
    # test = grouping_2021.merge(grouping_2020, how = 'outer', on = ['Particulars','As at 31.03.2020'])
    # test = test[test['groups_temp_x'].notna()]
    # test = test[test['groups_temp_y'].notna()]
    # test = test[~(test['Note No_x'].astype(str).str.contains('TOTAL'))]
    # test = test[~(test['Note No_y'].astype(str).str.contains('TOTAL'))]
    
    # test1 = test[test['groups_temp_x'] != test['groups_temp_y']]
    # wrong_mappings = test1[['groups_temp_x','groups_temp_y']].drop_duplicates().reset_index(drop = True)
    
    
    #Merge Groupings
    # count = 0
    # grouping_2020['group_no'] = 0
    # for i in range(1, len(grouping_2020)):
    #     if grouping_2020['groups'][i] == grouping_2020['groups'][i-1]:
    #         grouping_2020['group_no'][i] = count
    #     else:
    #         count = count + 1
    #         grouping_2020['group_no'][i] = count

    # count = 0
    # grouping_2021['group_no'] = 0
    # for i in range(1, len(grouping_2021)):
    #     if grouping_2021['groups'][i] == grouping_2021['groups'][i-1]:
    #         grouping_2021['group_no'][i] = count
    #     else:
    #         count = count + 1
    #         grouping_2021['group_no'][i] = count
                
    groups_2021 = grouping_2021['groups'].unique().tolist()
    groups_2020 = grouping_2020['groups'].unique().tolist()
    
    if len([item for item in groups_2021 if item not in groups_2020]) > 0:
        groups = groups_2021
    elif len([item for item in groups_2020 if item not in groups_2021]) >= 0:
        groups = groups_2020
    
    final_grouped = pd.DataFrame(columns = ['Particulars','Note No','As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019','groups'])
    #null_row = pd.DataFrame([[np.nan]*6],columns = final_grouped.columns)
    for group_name in groups:
        test = grouping_2020[grouping_2020['groups'] == group_name][['Particulars','Note No','As at 31.03.2020', 'As at 31.03.2019','groups_temp']]
        test1 = grouping_2021[grouping_2021['groups'] == group_name][['Particulars','As at 31.03.2021','As at 31.03.2020','groups_temp']]
        grouped = test1.merge(test, how = 'outer', on = ['Particulars','As at 31.03.2020'])
            
        group_heading = grouped[grouped['Particulars'] == group_name]
        grouped = grouped[grouped['Particulars'] != group_name]
        total = grouped[grouped['Note No'] == 'TOTAL']
        grouped = grouped[grouped['Note No'] != 'TOTAL']
        #grouped['note_no_temp'] = grouped['Note No'].combine_first(grouped['groups'])
        #grouped = grouped.sort_values(['Note No','As at 31.03.2021'],ascending=False)
        grouped = group_heading.append(grouped)
        grouped = grouped.append(total)
        grouped['groups'] = group_name
        grouped = grouped[final_grouped.columns.tolist()]
        grouped.loc[grouped['Particulars'] == grouped['groups'],'Note No'] = np.nan
        final_grouped = final_grouped.append(grouped)
        
    final_grouped = final_grouped.drop_duplicates()
    return final_grouped

final_grouped_notes = merge_groups(2020, 2021, 'Groupings')
final_grouped_creditors = merge_groups(2020, 2021, 'Creditor 2019-20')
final_grouped_debtors = merge_groups(2020, 2021, 'Debtor 2019-20')

final_grouped = final_grouped_notes.append([final_grouped_creditors,final_grouped_debtors])

# =============================================================================
# Part 2 - Statements
# =============================================================================

#Read Statements
df_2020 = clean(read_file(2020,'statement'),2020)
df_2021 = clean(read_file(2021,'statement'),2021)
cfs_2020 = clean_cfs(read_file(2020,'CashFlow'),2020)
cfs_2021 = clean_cfs(read_file(2021,'CashFlow'),2021)

df_2020 = cfs_2020.append(df_2020).reset_index(drop = True)
df_2021 = cfs_2021.append(df_2021).reset_index(drop = True)

statements = ['CASH FLOW STATEMENT',
              'BALANCE SHEET',
              'STATEMENT OF PROFIT AND LOSS',
              'NOTES TO FINANCIAL STATEMENT']

def separate(dataframe,i, statements):
    start = dataframe[(dataframe['Particulars'].str.contains(statements[i]).fillna(False)) |
                      (dataframe['Serial'].str.contains(statements[i]).fillna(False))].index[0]
    if i == len(statements)-1:
        fs = dataframe.iloc[start:]
    else:
        end = dataframe[dataframe['Particulars'].str.contains(statements[i+1]).fillna(False)].index[0]
        fs = dataframe.iloc[start:end]
        
    fs = fs.iloc[2:].reset_index(drop = True)
    return fs

dict_fs = {}
for i in range(len(statements)):
    
    fs_2020 = separate(df_2020,i,statements)
    fs_2021 = separate(df_2021,i,statements)
    
    fs = fs_2021.merge(fs_2020, how = 'outer').drop_duplicates()
    
    fs = fs[~((fs['Particulars'].isnull()) & 
              (fs['Note No'].isnull()))]
    
    fs['statement'] = statements[i]
    dict_fs[statements[i]] = fs

# =============================================================================
# Part 3 - Writing all statements and groupings to Excel
# =============================================================================

final = pd.concat([dict_fs[statements[0]],dict_fs[statements[1]],dict_fs[statements[2]]])
statements = final['statement'].unique().tolist()

writer = pd.ExcelWriter('Data Book 2019-21.xlsx', engine='xlsxwriter')

for statement in statements:
    df = final[final['statement'] == statement]
    df = df.drop(['statement'],axis = 1)
    df = df.dropna(axis = 1, how = 'all')

    df.to_excel(writer, sheet_name=statement,index = False)

final_grouped.drop(['groups'],axis = 1).to_excel(writer, sheet_name='GROUPINGS',index = False)
writer.save()

# =============================================================================
# Rough work/ Trial and Error
# =============================================================================
notes = dict_fs['NOTES TO FINANCIAL STATEMENT']

all_notes = notes[notes['Particulars'].fillna('').str.contains('NOTE ')][['Particulars']]
all_notes['Note'] = all_notes['Particulars'].fillna('').apply(lambda x : ''.join(filter(str.isdigit, x)))
all_notes['Note Name'] = all_notes['Particulars'].fillna('').str.partition(': ')[2]
notes = notes.merge(all_notes, how = 'left')
notes['Note'] = notes['Note'].ffill(axis = 0)
notes['Note Name'] = notes['Note Name'].ffill(axis = 0)

only_notes = final.copy()
only_notes['Note'] = only_notes['Note No'].str.strip('"')
only_notes = only_notes[only_notes['Note'].notna()]
only_notes = only_notes[~(only_notes['Note'].str.contains('[A-Za-z]+'))]
only_notes = only_notes[['Note','statement']]

y = notes.merge(only_notes, on = 'Note', how = 'left')
y = y[((y['As at 31.03.2021_x'].notna()) &
      (y['As at 31.03.2020_x'].notna()) &
      (y['As at 31.03.2019_x'].notna()))]
x = final_grouped.merge(y, how = 'left', left_on = ['As at 31.03.2021','As at 31.03.2020','As at 31.03.2019'],
                        right_on = ['As at 31.03.2021_x','As at 31.03.2020_x','As at 31.03.2019_x'])

notes_test = notes[(notes['As at 31.03.2021'].notna()) &
                   (notes['As at 31.03.2020'].notna()) &
                   (notes['As at 31.03.2019'].notna()) &
                   ((notes['As at 31.03.2021']!=0) |
                   (notes['As at 31.03.2020']!=0) |
                   (notes['As at 31.03.2019']!=0))]

x = final_grouped.merge(notes_test, how = 'left', on = ['As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']).merge(only_notes, how = 'left', on = 'Note')
x = x[x['Note No_x'] != x['Note No_y']]
z = x[(x['Note No_x'].notna()) |
      (x['Particulars_y'].notna())]

z = z[['groups','Particulars_y','Note','Note Name','statement_y']].drop_duplicates()
z = z[z['statement_y'] == 'BALANCE SHEET']

#Tag groupings to notes
#Tag notes to bs

#z = grouping_2020.merge(all_notes, left_on = 'Particulars', right_on = 'Note Name', how = 'left')

