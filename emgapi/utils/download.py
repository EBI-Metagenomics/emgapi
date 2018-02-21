DOWNLOAD_REF = {
    '1.0': {

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        '5SrRNA.fasta': {
            'display': 'ReadsEncoding-5s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '5S', 'real_ext': 'fasta',
            'suffix': '5SrRNA', 'ext': 'fasta'
        },
        '16SrRNA.fasta': {
            'display': 'ReadsEncoding-16s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '16S', 'real_ext': 'fasta',
            'suffix': '16SrRNA', 'ext': 'fasta'
        },
        '23SrRNA.fasta': {
            'display': 'ReadsEncoding-23s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '23S', 'real_ext': 'fasta',
            'suffix': '23SrRNA', 'ext': 'fasta'
        },
        'otu_table.tsv': {
            'display': 'OTUTable',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table', 'real_ext': 'txt',
            'suffix': 'otu_table', 'ext': 'tsv'
        },
        'otu_table_hdf5.biom': {
            'display': 'OTUTableHDF5',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_hdf5',
            'real_ext': 'biom',
            'suffix': 'otu_table_hdf5', 'ext': 'biom'
        },
        'otu_table_json.biom': {
            'display': 'OTUTableJSON',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_json',
            'real_ext': 'biom',
            'suffix': 'otu_table_json', 'ext': 'biom'
        },
        'pruned.tree': {
            'display': 'PhylogeneticTree',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'pruned', 'real_ext': 'tree',
            'suffix': 'pruned', 'ext': 'tree'
        },

    },
    '2.0': {
        # sequence data files
        # 'PROCESSED_READS': {},
        # 'READS_WITH_PREDICTED_CDS': { },
        # 'READS_WITH_MATCHES_FASTA': { },
        # 'READS_WITHOUT_MATCHES_FASTA': { },
        # 'PREDICTED_CDS': { },
        # 'PREDICTED_CDS_WITHOUT_ANNOTATION': { },
        # 'PREDICTED_ORF_WITHOUT_ANNOTATION': { },

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        '5SrRNA.fasta': {
            'display': 'ReadsEncoding-5s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '5S', 'real_ext': 'fasta',
            'suffix': '5SrRNA', 'ext': 'fasta'
        },
        '16SrRNA.fasta': {
            'display': 'ReadsEncoding-16s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '16S', 'real_ext': 'fasta',
            'suffix': '16SrRNA', 'ext': 'fasta'
        },
        '23SrRNA.fasta': {
            'display': 'ReadsEncoding-23s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '23S', 'real_ext': 'fasta',
            'suffix': '23SrRNA', 'ext': 'fasta'
        },
        'otu_table.tsv': {
            'display': 'OTUTable',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table', 'real_ext': 'txt',
            'suffix': 'otu_table', 'ext': 'tsv'
        },
        'otu_table_hdf5.biom': {
            'display': 'OTUTableHDF5',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_hdf5',
            'real_ext': 'biom',
            'suffix': 'otu_table_hdf5', 'ext': 'biom'
        },
        'otu_table_json.biom': {
            'display': 'OTUTableJSON',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_json',
            'real_ext': 'biom',
            'suffix': 'otu_table_json', 'ext': 'biom'
        },
        'pruned.tree': {
            'display': 'PrunedTree',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'pruned', 'real_ext': 'tree',
            'suffix': 'pruned', 'ext': 'tree'
        },

    },
    '3.0': {

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        '5SrRNA.fasta': {
            'display': 'ReadsEncoding-5s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '5S', 'real_ext': 'fasta',
            'suffix': '5SrRNA', 'ext': 'fasta'
        },
        '16SrRNA.fasta': {
            'display': 'ReadsEncoding-16s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '16S', 'real_ext': 'fasta',
            'suffix': '16SrRNA', 'ext': 'fasta'
        },
        '23SrRNA.fasta': {
            'display': 'ReadsEncoding-23s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '23S', 'real_ext': 'fasta',
            'suffix': '23SrRNA', 'ext': 'fasta'
        },
        'otu_table.tsv': {
            'display': 'OTUTable',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table', 'real_ext': 'txt',
            'suffix': 'otu_table', 'ext': 'tsv'
        },
        'otu_table_hdf5.biom': {
            'display': 'OTUTableHDF5',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_hdf5',
            'real_ext': 'biom',
            'suffix': 'otu_table_hdf5', 'ext': 'biom'
        },
        'otu_table_json.biom': {
            'display': 'OTUTableJSON',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_json',
            'real_ext': 'biom',
            'suffix': 'otu_table_json', 'ext': 'biom'
        },
        'pruned.tree': {
            'display': 'PrunedTree',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'pruned', 'real_ext': 'tree',
            'suffix': 'pruned', 'ext': 'tree'
        },

    },
    '4.0': {

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        '5SrRNA.fasta': {
            'display': 'ReadsEncoding-5s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '5S', 'real_ext': 'fasta',
            'suffix': '5SrRNA', 'ext': 'fasta'
        },
        '16SrRNA.fasta': {
            'display': 'ReadsEncoding-16s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '16S', 'real_ext': 'fasta',
            'suffix': '16SrRNA', 'ext': 'fasta'
        },
        '23SrRNA.fasta': {
            'display': 'ReadsEncoding-23s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '23S', 'real_ext': 'fasta',
            'suffix': '23SrRNA', 'ext': 'fasta'
        },
        'otu_table.tsv': {
            'display': 'OTUTable',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table', 'real_ext': 'txt',
            'suffix': 'otu_table', 'ext': 'tsv'
        },
        'otu_table_hdf5.biom': {
            'display': 'OTUTableHDF5',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_hdf5',
            'real_ext': 'biom',
            'suffix': 'otu_table_hdf5', 'ext': 'biom'
        },
        'otu_table_json.biom': {
            'display': 'OTUTableJSON',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_json',
            'real_ext': 'biom',
            'suffix': 'otu_table_json', 'ext': 'biom'
        },
        'pruned.tree': {
            'display': 'PrunedTree',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'pruned', 'real_ext': 'tree',
            'suffix': 'pruned', 'ext': 'tree'
        },

    },
    '4.1': {

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_name': True, 'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        '5SrRNA.fasta': {
            'display': 'ReadsEncoding-5s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '5S', 'real_ext': 'fasta',
            'suffix': '5SrRNA', 'ext': 'fasta'
        },
        '16SrRNA.fasta': {
            'display': 'ReadsEncoding-16s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '16S', 'real_ext': 'fasta',
            'suffix': '16SrRNA', 'ext': 'fasta'
        },
        '23SrRNA.fasta': {
            'display': 'ReadsEncoding-23s',
            'subdir': 'sequence-categorisation',
            'real_name': False, 'real_suffix': '23S', 'real_ext': 'fasta',
            'suffix': '23SrRNA', 'ext': 'fasta'
        },
        'otu_table.tsv': {
            'display': 'OTUTable',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table', 'real_ext': 'txt',
            'suffix': 'otu_table', 'ext': 'tsv'
        },
        'otu_table_hdf5.biom': {
            'display': 'OTUTableHDF5',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_hdf5',
            'real_ext': 'biom',
            'suffix': 'otu_table_hdf5', 'ext': 'biom'
        },
        'otu_table_json.biom': {
            'display': 'OTUTableJSON',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'otu_table_json',
            'real_ext': 'biom',
            'suffix': 'otu_table_json', 'ext': 'biom'
        },
        'pruned.tree': {
            'display': 'PrunedTree',
            'subdir': 'cr_otus',
            'real_name': True, 'real_suffix': 'pruned', 'real_ext': 'tree',
            'suffix': 'pruned', 'ext': 'tree'
        },

    },
}
