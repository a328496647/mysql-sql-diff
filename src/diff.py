#coding: utf-8
import os, sys
import json
import re
import copy
import mysql_diff

m_file = sys.argv[1]
s_file = sys.argv[2]

with open(m_file, 'r') as f:
    m_tables = mysql_diff.parse_sql(f.readlines())

with open(s_file, 'r') as f:
    s_tables = mysql_diff.parse_sql(f.readlines())

for m_table_key in m_tables:
    m_table = m_tables[m_table_key]
    m_field_sort = m_table['field_sort']
    m_fields = m_table['fields']

    if not s_tables.has_key(m_table_key):
        print m_table['sql']
        continue

    s_table = s_tables[m_table_key]
    s_field_sort = s_table['field_sort']
    s_fields = s_table['fields']

    sql = ''

    # DROP COLUMN
    s_i = 0
    while s_i < len(s_field_sort):
        s_field_key = s_field_sort[s_i]
        if not s_field_key in m_field_sort:
            sql += "DROP COLUMN `" + s_fields[s_field_key].name + "`,\n"
            s_field_sort.pop(s_i)
        else:
            s_i += 1
    """
    # ADD COLUMN
    for m_i in range(0, len(m_field_sort)):
        m_field_key = m_field_sort[m_i]
        if not m_field_key in s_field_sort:
            sql += "ADD COLUMN " + str(m_fields[m_field_key]) + (" AFTER `" + m_fields[m_field_sort[m_i - 1]].name + "`" if m_i > 0 else " FIRST") + ",\n"
            s_field_sort.insert(m_i, m_field_key)
    """
    # CHANGE COLUMN
    for m_i in range(0, len(m_field_sort)):
        m_field_key = m_field_sort[m_i]
        m_field = m_fields[m_field_key]
        m_field_sql = str(m_field)
        
        if not m_field_key in s_field_sort:
            sql += "ADD COLUMN " + str(m_fields[m_field_key]) + (" AFTER `" + m_fields[m_field_sort[m_i - 1]].name + "`" if m_i > 0 else " FIRST") + ",\n"
            s_field_sort.insert(m_i, m_field_key)
            continue

        s_i = s_field_sort.index(m_field_key)
        s_field = s_fields[m_field_key]
        s_field_sql = str(s_field)

        m_prev_field_key = m_field_sort[m_i - 1] if m_i > 0 else None
        s_prev_field_key = s_field_sort[s_i - 1] if s_i > 0 else None

        if m_field_sql == s_field_sql and m_prev_field_key == s_prev_field_key:
            continue

        sql += "CHANGE `" + s_field.name + "` " + m_field_sql
        
        if m_prev_field_key != s_prev_field_key:
            if m_prev_field_key != None:
                sql += " AFTER `" + m_fields[m_prev_field_key].name + "`"
            else:
                sql += " FIRST"

            s_field_sort.pop(s_i)
            s_field_sort.insert(m_i, m_field_key)

        sql += ",\n"

    m_keys = m_table['keys']
    s_keys = s_table['keys']
    
    # DROP INDEX
    for s_key_key in s_keys:
       s_key = s_keys[s_key_key]
       if not m_keys.has_key(s_key_key):
            if s_key.type != 'PRIMARY':
                sql += "DROP INDEX `" + s_key.name + "`,\n"
            else:
                sql += "DROP PRIMARY KEY,\n"

    for m_key_key in m_keys:
    
        m_key = m_keys[m_key_key]
        m_key_sql = str(m_key)

        # ADD INDEX
        if not s_keys.has_key(m_key_key):
            sql += "ADD " + m_key_sql + ",\n"
            continue
            
        # CHANGE INDEX
        s_key = s_keys[m_key_key]
        s_key_sql = str(s_key)
        
        if m_key_sql == s_key_sql:
            continue
        
        sql += "DROP INDEX `" + s_key.name + "`,\n"
        sql += "ADD " + m_key_sql + ",\n"

    if sql != '':
        print "ALTER TABLE `"+ s_table['name'] +"`\n" + sql[0:-2] + ";\n"