import os
import pathlib

import logging


class DownloadFile:
    def __init__(self):
        self.realname = None
        self.alias = None
        self.description_label = None
        self.file_format = None
        self.compression = None
        self.group_type = None
        self.sub_dir = None
        self.result_dir = None
        self.required = None

    def __init_properties(self, file_config, result_dir, realname, alias):
        self.realname = realname
        self.alias = alias
        self.result_dir = result_dir
        self.description_label = file_config['description_label']
        # self.file_format = ''.join(pathlib.Path(realname).suffixes)
        self.file_format = file_config['format_name']
        self.compression = file_config['compression']
        self.group_type = file_config['group_type']
        self.sub_dir = file_config['subdir'] or ''
        self.required = file_config['_required']

    def unchunked_file(self, file_config, result_dir, input_file_name):
        if file_config['_accession_substitution'] == 'accession':
            input_file_name = input_file_name.split('_').pop(0)
        realname = file_config['real_name']
        _realname = realname.format(input_file_name) if '{}' in realname else realname
        _alias = file_config['alias'].format(input_file_name)
        self.__init_properties(file_config, result_dir, _realname, _alias)

    def chunked_file(self, file_config, result_dir, realname, alias):
        self.__init_properties(file_config, result_dir, realname, alias)


class UnchunkedDownloadFile(DownloadFile):
    def __init__(self, file_config, result_dir, input_file_name):
        super().__init__()
        super().unchunked_file(file_config, result_dir, input_file_name)


class ChunkedDownloadFile(DownloadFile):
    def __init__(self, file_config, result_dir, realname, alias):
        super().__init__()
        super().chunked_file(file_config, result_dir, realname, alias)


class ChunkedDownloadFiles:
    def __init__(self, file_config, result_dir, input_file_name):
        self.parent_file = None
        self.chunked_files = []
        if file_config['_accession_substitution'] == 'accession':
            input_file_name = input_file_name.split('_').pop(0)

        sub_dir = file_config['subdir'] or ''

        chunk_filename = file_config['chunk_file']
        if '{}' in chunk_filename:
            chunk_filename = chunk_filename.format(input_file_name)

        chunk_filepath = os.path.join(result_dir, sub_dir, chunk_filename)
        if os.path.exists(chunk_filepath):
            chunks = self.read_chunkfile(chunk_filepath)
            if len(chunks) == 1:
                alias = file_config['alias'].format(input_file_name)
                realname = chunks[0]
                realname = realname.format(input_file_name) if '{}' in realname else realname
                new_file = ChunkedDownloadFile(file_config, result_dir, realname, alias)
                self.chunked_files.append(new_file)
            else:
                # Added parent file
                alias = self.get_alias(1, file_config['alias'], input_file_name)
                realname = chunks.pop(0)
                self.parent_file = ChunkedDownloadFile(file_config, result_dir, realname, alias)
                # Add remaining files
                for i, realname in enumerate(chunks, start=2):
                    alias = self.get_alias(i, file_config['alias'], input_file_name)
                    child_file = ChunkedDownloadFile(file_config, result_dir, realname, alias)
                    self.chunked_files.append(child_file)
        else:
            logging.warning('.chunks file does not exist: {}'.format(chunk_filepath))

    @staticmethod
    def get_alias(file_num, alias, input_file_name):
        fmt_name = alias.format(input_file_name)
        name_path = pathlib.Path(fmt_name)
        alias = name_path.name
        final_suffix = ""
        for suffix in name_path.suffixes:
            alias = alias.replace(suffix, "")
            final_suffix += suffix
        return alias + '_' + str(file_num) + final_suffix

    @staticmethod
    def read_chunkfile(filename):
        with open(filename) as f:
            return [l.strip() for l in f.readlines()]
