#!/usr/bin/env python
# -*- coding:utf-8 -*-
from app.utils.DBHelper import MyHelper


class GeneralVoucherDao:
    @classmethod
    def general_voucher_to_dict(cls, data):
        """
        将general_voucher表中查询出的全部结果转为字典数组
        :param data: 查询到的结果
        :return: 数组类型，每一个元素是表中一行转为字典后的结果
        """
        result = []
        for row in data:
            result.append({
                'date': row[0],
                'record_date': row[1],
                'voucher_no': row[2],
                'attachments_number': row[3],
                'checked': row[4]
            })
        return result

    @classmethod
    def voucher_entry_to_dict(cls, data):
        """
        将voucher_entry表中查询出的全部结果转为字典数组
        :param data: 查询到的结果
        :return: 数组类型，每一个元素是表中一行转为字典后的结果
        """
        result = []
        for row in data:
            result.append({
                'voucher_no': row[0],
                'abstract': row[1],
                'subject_code': row[2],
                'credit_debit': row[3],
                'total': row[4]
            })
        return result

    def insert_voucher(self, data):
        """
        插入新的凭证，包括其各个分录
        :param data: 字典类型，date: 凭证日期，voucher_no：凭证编号, attachments_no：凭证附件数, entries: 凭证分录数组
        entries每一个元素仍为字典, abstract: 分录摘要, subject_code: 分录科目代码, credit_debit：分录金额为"借"/"贷"
                                    total: 分录总金额
        :return: tuple类型, 第一个元素表示是否插入成功, 若成功第二个元素则返回所有数据, 否则第二个元素返回错误信息
        """
        conn = MyHelper()
        if (not all([data.get('date'), data.get('voucher_no'), data.get('attachments_number') is not None, data.get('entries')])) \
                or (data.get('entries') and len(data.get('entries')) == 0):
            return False, '凭证信息不全'

        sqls = ["insert into general_voucher (date, voucher_no, attachments_number) "
                "values (%s, %s, %s)"]
        params = [[data.get('date'), data.get('voucher_no'), data.get('attachments_number')]]

        for entry in data.get('entries'):
            if not all([entry.get('abstract'), entry.get('subject_code'), entry.get('credit_debit'), entry.get('total')]):
                return False, '分录信息不全'
            sqls.append("insert into voucher_entry (voucher_no, abstract, subject_code, credit_debit, total) "
                        "values (%s, %s, %s, %s, %s)")
            params.append([data.get("voucher_no"), entry.get('abstract'), entry.get('subject_code'),
                           entry.get('credit_debit'), entry.get('total')])

        rows = conn.executeUpdateTransaction(sqls=sqls, params=params)
        if rows:
            return True, data
        else:
            return False, '凭证编号重复或凭证及分录信息有误'

    def query_voucher(self, cond={}):
        """
        查询凭证信息（仅限于general_voucher表中信息，不包含凭证）
        :param cond: 查询条件，可以放入任意general_voucher表中已有的字段
        :return: tuple，返回地查询结果
        """
        conn = MyHelper()
        params = []

        sql = "select * from general_voucher where 1 = 1"
        cond = cond or {}
        if cond.get('date'):
            sql += " and date = %s"
            params.append(cond.get('date'))
        if cond.get('record_date'):
            sql += " and record_date = %s"
            params.append(cond.get('record_date'))
        if cond.get('voucher_no'):
            sql += " and voucher_no = %s"
            params.append(cond.get('voucher_no'))
        if cond.get('attachments_number'):
            sql += " and attachments_number = %s"
            params.append(cond.get('attachments_number'))
        if cond.get('checked'):
            sql += " and checked = %s"
            params.append(cond.get('checked'))

        sql += ' order by voucher_no asc'
        return conn.executeQuery(sql=sql, param=params)

    def query_voucher_entries(self, cond={}):
        """
        查询凭证的分录信息
        :param cond: 查询条件，可以放入任意voucher_entry表中已有的字段
        :return: tuple类型, 查询voucher_entry表中直接返回的结果
        """
        conn = MyHelper()
        params = []

        sql = "select * from voucher_entry where 1 = 1"
        if cond.get('voucher_no'):
            sql += " and voucher_no = %s"
            params.append(cond.get('voucher_no'))
        if cond.get('abstract'):
            sql += " and abstract = %s"
            params.append(cond.get('abstract'))
        if cond.get('subject_code'):
            sql += " and subject_code = %s"
            params.append(cond.get('subject_code'))
        if cond.get('credit_debit'):
            sql += " and credit_debit = %s"
            params.append(cond.get('credit_debit'))
        if cond.get('total'):
            sql += " and total = %s"
            params.append(cond.get('total'))

        sql += ' order by voucher_no, subject_code asc'
        return conn.executeQuery(sql=sql, param=params)

    def update_voucher(self, voucher_no, data):
        """
        更新凭证信息
        :param  voucher_no: 所更新的凭证的凭证编号
        :param  data: 同insert_voucher的参数，general_voucher所有字段选填；entries字段若存在则表示
                    更新后的凭证的所有分录
        :return: tuple类型，第一个元素表示是否更新成功。若成功，则第二、第三个元素分别代表更新前的信息和更新后的信息；
                                                        否则，第二个元素返回出错信息
        """
        if not voucher_no:
            return False, "缺少凭证号参数"
        conn = MyHelper()
        voucher = self.query_voucher({'voucher_no': voucher_no})
        if not voucher:
            return False, '凭证号错误，找不到该凭证'
        old_data = self.general_voucher_to_dict(voucher)[0]
        new_data = old_data.copy()
        entries = self.query_voucher_entries({'voucher_no': voucher_no})
        if not entries:
            entries = []
        old_data['entries'] = self.voucher_entry_to_dict(entries)

        sqls = []
        params = []
        # 若数据中关于凭证的其他字段不为空，则更新凭证
        if not (data.get('voucher_no') is None and data.get('date') is None and data.get('record_date') is None \
            and data.get('attachments_number') is None and data.get('checked') is None):
            sql = "update general_voucher set "
            param = []
            if data.get('voucher_no') is not None:
                sql += "voucher_no = %s, "
                param.append(data.get('voucher_no'))
                new_data['voucher_no'] = data.get('voucher_no')
            if data.get('date') is not None:
                sql += "date = %s, "
                param.append(data.get('date'))
                new_data['date'] = data.get('date')
            if data.get('record_date') is not None:
                sql += "record_date = %s, "
                param.append(data.get('record_date'))
                new_data["record_date"] = data.get('record_date')
            if data.get('attachments_number') is not None:
                sql += "attachments_number = %s, "
                param.append(data.get('attachments_number'))
                new_data['attachments_number'] = data.get('attachments_number')
            if data.get('checked') is not None:
                sql += "checked = %s, "
                param.append(data.get('checked'))
                new_data['checked'] = data.get('checked')
            sql += "voucher_no = voucher_no where voucher_no = %s"
            param.append(voucher_no)
            sqls.append(sql)
            params.append(param)
        # 若数据中含有分录字段，则更新分录，采用先全部删除，后进行添加的方式
        if data.get('entries') and len(data.get('entries')):
            sqls.append("delete from voucher_entry where voucher_no = %s")
            params.append([data.get('voucher_no')])
            for entry in data.get('entries'):
                if not all([entry.get('abstract'), entry.get('subject_code'), entry.get('credit_debit'),
                            entry.get('total')]):
                    return False, '分录信息不全'
                sqls.append("insert into voucher_entry (voucher_no, abstract, subject_code, credit_debit, total) "
                            "values (%s, %s, %s, %s, %s)")
                params.append([data.get("voucher_no"), entry.get('abstract'), entry.get('subject_code'),
                               entry.get('credit_debit'), entry.get('total')])
            new_data['entries'] = data.get('entries')

        rows = conn.executeUpdateTransaction(sqls=sqls, params=params)
        if rows:
            return True, old_data, new_data
        else:
            return False, '凭证信息错误或重复，更新无效'

    def delete_voucher(self, voucher_no):
        """
        删除凭证及其分录
        :param voucher_no: 所删除的凭证的凭证编号
        :return: tuple类型，第一个参数为操作是否正确，第二个参数在正确时表为所删除的数据，失败时为错误信息
        """
        voucher = self.query_voucher({'voucher_no': voucher_no})
        if not voucher:
            return False, '凭证号错误，找不到该凭证'

        old_data = self.general_voucher_to_dict(voucher)[0]
        entries = self.query_voucher_entries({'voucher_no': voucher_no})
        if not entries:
            entries = []
        old_data['entries'] = self.voucher_entry_to_dict(entries)

        # 数据库中已定义 on delete cascade，分录无需重复删除
        conn = MyHelper()
        if conn.executeUpdate(
            sql='delete from general_voucher where voucher_no = %s',
            param=[voucher_no]
        ):
            return True, old_data
        else:
            return False, '出现未知错误，找不到该凭证'