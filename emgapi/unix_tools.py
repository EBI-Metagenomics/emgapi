#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import re

def awk_range(file, col, gt, lt):
    """
    Filter a file by a column based on a range.

    For example:
    `awk '{ if ($2 > 100 && $2 < 1000) print $0}' fasta.faix
    """
    flt = '{{ if (${col} > {gt} && ${col} < {lt}) print $0}}' \
        .format(col=col, gt=gt, lt=lt)
    return awk(file, criteria=flt)

def awk_regex_filter(file, regex):
    """
    Filter a file by a using a regex.

    For example, on a gff attributes field by COG category: /COG=.*G/
    """
    flt = '{{ if ($0 ~ {regex}) print $1 }}'.format(regex=regex)
    return awk(file, flt)

def awk(file, criteria):
    """Run an awk command using subprocess.

    Timeout 5 seconds. 
    """
    # FIXME: check efficiency
    args = ['awk', criteria, file]
    result = subprocess.check_output(args, universal_newlines=True, shell=False, timeout=5)
    return result.splitlines()
