# -*- coding: utf-8 -*-
"""
Created on Thu May 12 21:55:45 2022

@author: naman
"""

import pandas as pd
import numpy as np
import os
import re

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
    df = df[~(df['Particulars'].isin(['(CIN NO : )','(INDIA) PRIVATE LIMITED','MW. COM (INDIA) PRIVATE LIMITED']))]
    
    return df

def clean_groupings(grouping_df,year):
    
    grouping_df = grouping_df.iloc[2:]
    grouping_df = grouping_df[grouping_df['Particulars'] != 'TRADE RECEIVABLES']
    grouping_df = grouping_df[~(grouping_df['Particulars'].str.contains('GROUPING TO THE FINANCIAL STATEMENT AS AT').fillna(False))]
    grouping_df.loc[grouping_df['As at 31.03.'+str(year)].notna(),'As at 31.03.'+str(year-1)] = grouping_df['As at 31.03.'+str(year-1)].fillna(0)
    grouping_df.loc[grouping_df['As at 31.03.'+str(year-1)].notna(),'As at 31.03.'+str(year)] = grouping_df['As at 31.03.'+str(year)].fillna(0)    
    grouping_df = grouping_df[grouping_df['As at 31.03.'+str(year)] != 'As at']
    grouping_df['groups'] = grouping_df['As at 31.03.'+str(year-1)].isnull().astype(int).cumsum()
    grouping_df.loc[grouping_df['As at 31.03.'+str(year-1)].notnull(),'groups'] = np.nan
    grouping_df.loc[grouping_df['groups'].notnull(),'groups'] = grouping_df['Particulars']
    grouping_df['groups'] = grouping_df['groups'].ffill(axis = 0)
    
    grouping_df['Particulars'] = grouping_df['Particulars'].combine_first(grouping_df['Note No'])
    grouping_df.loc[grouping_df['Particulars'].fillna('').str.lower().str.contains('total'),'Note No'] = grouping_df['Note No'].combine_first(grouping_df['Particulars'])
    
    grouping_df['temp_note'] = grouping_df['Note No'].str.lower().str.replace('sub','').str.replace(' ','').str.lstrip().str.upper()
    grouping_df['string_len'] = grouping_df['temp_note'].fillna('').apply(len)
    grouping_df.loc[(grouping_df['Note No'].str.contains('TOTAL')) &
                    (grouping_df['string_len'] > 8), 'Note No'] = 'TOTAL'
    
    grouping_df = grouping_df.drop(['temp_note','string_len'],axis = 1)
    
    null_row = pd.DataFrame([[np.nan]*len(grouping_df.columns)],columns = grouping_df.columns)    
    grouping_df = grouping_df.append(null_row)

    grouping_df.loc[(grouping_df['As at 31.03.'+str(year)].isnull()) &
                    (grouping_df['As at 31.03.'+str(year-1)].isnull()),'temp_total'] = 'TOTAL'
    
    grouping_df['temp_total'] = grouping_df['temp_total'].shift(-1)
    grouping_df['Note No'] = grouping_df['Note No'].combine_first(grouping_df['temp_total'])
    grouping_df = grouping_df.drop(['temp_total'],axis = 1)
    grouping_df.loc[grouping_df['Particulars'] == grouping_df['groups'],'Note No'] = np.nan
    
    x = grouping_df[grouping_df['Particulars'] == grouping_df['groups']].iloc[:1]
    x['major_group'] = x['groups']
    
    grouping_df = grouping_df.merge(x, how = 'left')
    
    # def clean_notes(strValue):
    #     return re.sub('[\(\[].*?[\)\]]', '', strValue.lower()).strip()
    # grouping_df['temp_note'] = grouping_df['Note No'].fillna('').apply(clean_notes)
    # grouping_df.loc[grouping_df['temp_note'] != 'total','temp_note'] = np.nan
 
    grouping_df['temp_note'] = grouping_df['Note No'].shift()
    grouping_df.loc[grouping_df['temp_note'].str.lower().str.strip() == 'total','major_group'] = grouping_df['Particulars']
    grouping_df['major_group'] = grouping_df['major_group'].ffill(axis = 0)
    grouping_df = grouping_df.drop(['temp_note'],axis = 1)

    
    grouping_df['major_group'].iloc[-1] = np.nan
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
    
    groups_2021 = grouping_2021['major_group'].dropna().unique().tolist()
    groups_2020 = grouping_2020['major_group'].dropna().unique().tolist()
    
    if len([item for item in groups_2021 if item not in groups_2020]) > 0:
        groups = groups_2021
    elif len([item for item in groups_2020 if item not in groups_2021]) >= 0:
        groups = groups_2020
    
    final_grouped = pd.DataFrame(columns = ['Particulars','Note No','As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019','groups','major_group','sheet_name'])

    for group_name in groups:

        test = grouping_2020[grouping_2020['major_group'] == group_name]
        test1 = grouping_2021[grouping_2021['major_group'] == group_name]
        
        for sub_group in test['groups'].unique().tolist():

            test_sub = test[test['groups'] == sub_group][['Particulars','As at 31.03.2020', 'As at 31.03.2019','groups','major_group']]
            test1_sub = test1[test1['groups'] == sub_group][['Particulars','Note No','As at 31.03.2021','As at 31.03.2020','groups','major_group']]
            
            grouped = test1_sub.merge(test_sub, how = 'outer', on = ['Particulars','As at 31.03.2020','groups','major_group'])
            cols = grouped.columns.tolist()
            
            group_heading = grouped[grouped['Particulars'] == sub_group]
            grouped = grouped[grouped['Particulars'] != sub_group]
            total = grouped[grouped['Note No'].fillna('').str.lower().str.contains('total')]
            grouped = grouped[~(grouped['Note No'].fillna('').str.lower().str.contains('total'))]            
            grouped[['As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019']] = grouped[['As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019']].fillna(0)
            grouped = grouped.groupby(['Particulars','groups','major_group'],as_index = False)[['As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019']].sum()
            grouped['Note No'] = np.nan
            if len(grouped) == 0:
                grouped = pd.DataFrame(columns = cols)
            else:
                grouped = grouped[cols]
            grouped = grouped.sort_values(['As at 31.03.2021', 'As at 31.03.2020','As at 31.03.2019'],ascending=False)
            grouped = group_heading.append(grouped)
            grouped = grouped.append(total)
            grouped['groups'] = sub_group
            grouped['major_group'] = group_name
            grouped['sheet_name'] = sheet_name
            grouped = grouped[final_grouped.columns.tolist()]
            grouped.loc[grouped['Particulars'] == grouped['groups'],'Note No'] = np.nan
            final_grouped = final_grouped.append(grouped)
        
    final_grouped = final_grouped[final_grouped['As at 31.03.2020']!='As at']
    final_grouped = final_grouped.drop_duplicates()

    return final_grouped

final_grouped_notes = merge_groups(2020, 2021, 'Groupings')
final_grouped_creditors = merge_groups(2020, 2021, 'Creditor 2019-20')
final_grouped_debtors = merge_groups(2020, 2021, 'Debtor 2019-20')

sheet_name = 'Groupings'

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

#final_grouped.drop(['groups'],axis = 1).to_excel(writer, sheet_name='GROUPINGS_ALL',index = False)

# =============================================================================
# Rough work/ Trial and Error
# =============================================================================
notes = dict_fs['NOTES TO FINANCIAL STATEMENT']
notes = notes[~(notes['Particulars'].str.contains('FOR THE YEAR ENDED').fillna(False))]

all_notes = notes[notes['Particulars'].fillna('').str.contains('NOTE ')][['Particulars']]
all_notes['Note'] = all_notes['Particulars'].fillna('').apply(lambda x : ''.join(filter(str.isdigit, x)))
all_notes['Note Name'] = all_notes['Particulars'].fillna('').str.partition(': ')[2]
notes = notes.merge(all_notes, how = 'left')
notes['Note'] = notes['Note'].ffill(axis = 0)
notes['Note Name'] = notes['Note Name'].ffill(axis = 0)

notes.loc[(notes['As at 31.03.2021'].isnull()) &
          (notes['As at 31.03.2020'].isnull()) &
          (notes['As at 31.03.2019'].isnull()),'Group Name'] = notes['Particulars']
notes['Group Name'] = notes['Group Name'].ffill(axis = 0)

notes = notes.drop(['Serial','statement'],axis = 1)

notes_test = notes[(notes['As at 31.03.2021'].notna()) &
                   (notes['As at 31.03.2020'].notna()) &
                   (notes['As at 31.03.2019'].notna()) &
                   ((notes['As at 31.03.2021']!=0) |
                   (notes['As at 31.03.2020']!=0) |
                   (notes['As at 31.03.2019']!=0))]

x1 = final_grouped.merge(notes_test, how = 'left', on = ['As at 31.03.2021','As at 31.03.2020','As at 31.03.2019'])
x1 = x1[x1['Note No_x'] != x1['Note No_y']]
z = x1[(x1['Note No_x'].notna()) |
      (x1['Particulars_y'].notna())]

z = x1[(x1['Note No_x'].notna()) |
      (x1['Particulars_y'].notna())]

z = z[['groups','major_group','Particulars_y','Note','Note Name','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019','sheet_name']].drop_duplicates()

z['Note Name'] = z.groupby(['major_group'])['Note Name'].bfill()
z['Note Name'] = z.groupby(['major_group'])['Note Name'].ffill()

w = z[['Note Name','Particulars_y','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']].drop_duplicates().dropna()
q = notes.merge(w, how = 'left')
q = q[q['Particulars']!=q['Group Name']]
q = q[(q['Particulars_y'].isnull()) &
      (q['Note No'] != 'TOTAL')]

combs = z[['groups','major_group','Note Name']].dropna().drop_duplicates()
final_grouped = final_grouped.merge(combs, how = 'left')

q = q.drop(['Group Name','Note No'],axis = 1)
q['Particulars_y'] = q['Particulars']
q['groups'] = q['Particulars']
q['major_group'] = q['Note Name']
q['sheet_name'] = np.nan
q = q.drop(['Particulars'],axis = 1)

z = z.append(q)
    
xyz = z[['Note','Note Name']].drop_duplicates().dropna().reset_index(drop = True)
z = z.drop('Note',axis = 1).merge(xyz, on = 'Note Name', how = 'left')

nulls = z[z['Particulars_y'].isnull()]
non_nulls = z[z['Particulars_y'].notna()]
non_nulls['Note'] = non_nulls['Note'].astype(int)
nulls = nulls[~nulls['major_group'].isin(non_nulls['major_group'].drop_duplicates().tolist())]

groups = non_nulls.sort_values('Note')['Note Name'].dropna().unique().tolist()

for group_name in groups:
    abc = non_nulls[non_nulls['Note Name'] == group_name].drop_duplicates()
    abc = abc[['Note Name','Particulars_y','major_group','Note','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']].drop_duplicates()
    if len(group_name) > 30:
        sheet_name = re.sub('[\(\[\)\]]', '', group_name).replace(' ','').replace('/','_')[0:30]
    else:
        sheet_name = group_name
    
    abc.to_excel(writer, sheet_name = sheet_name,index = False)
    workbook  = writer.book
    worksheet = writer.sheets[sheet_name]
    
    row_idx, col_idx = abc.shape
    for r in range(row_idx):
        for c in range(col_idx):
            worksheet.write(r + 3, c, abc.values[r, c], workbook.add_format({'border': 1, 'num_format': '0.00'}))

    worksheet.set_column(0, col_idx, 12)
    startrow = len(abc) + 5
    abc = abc[['major_group','Particulars_y','Note','Note Name']]
    final_grouped_merged = final_grouped.merge(abc, on = ['major_group','Note Name'])
    
    #final_grouped_merged = final_grouped_merged[final_grouped_merged['Note No'] !='TOTAL'].drop('groups',axis = 1).drop_duplicates()

    for sub_group in final_grouped_merged['Particulars_y'].unique().tolist():
        test_sub = final_grouped_merged[final_grouped_merged['Particulars_y'] == sub_group]
        test_sub = test_sub[['Particulars','Note No','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']]
        test_sub.to_excel(writer, sheet_name = sheet_name,index = False, startrow = startrow)
        startrow = startrow + len(test_sub) + 5

groups = nulls['sheet_name'].dropna().unique().tolist()

for group_name in groups:
    abc = nulls[nulls['sheet_name'] == group_name].drop_duplicates()
    abc = abc[['Note Name','Particulars_y','major_group','Note','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']].drop_duplicates()

    abc.to_excel(writer, sheet_name = group_name,index = False)
    
    startrow = len(abc) + 5
    abc = abc[['major_group','Particulars_y']]
    final_grouped_merged = final_grouped.merge(abc, on = ['major_group'])    
    #final_grouped_merged = final_grouped_merged[final_grouped_merged['Note No'] !='TOTAL'].drop('groups',axis = 1).drop_duplicates()

    for sub_group in final_grouped_merged['major_group'].unique().tolist():
        test_sub = final_grouped_merged[final_grouped_merged['major_group'] == sub_group]        
        test_sub = test_sub[['Particulars','Note No','As at 31.03.2021','As at 31.03.2020','As at 31.03.2019']]
        test_sub.to_excel(writer, sheet_name = group_name,index = False, startrow = startrow)
        startrow = startrow + len(test_sub) + 5

writer.save()
