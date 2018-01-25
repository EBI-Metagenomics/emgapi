DOWNLOAD_REF = {
    '2.0': {

        # sequence data files
        # 'PROCESSED_READS': { },
        # 'READS_WITH_PREDICTED_CDS': { },
        # 'READS_WITH_MATCHES_FASTA': { },
        # 'READS_WITHOUT_MATCHES_FASTA': { },
        # 'PREDICTED_CDS': { },
        # 'PREDICTED_CDS_WITHOUT_ANNOTATION': { },
        # 'PREDICTED_ORF_WITHOUT_ANNOTATION': { },

        # functional result files
        'InterPro.tsv': {
            'display': 'InterProMatches',
            'real_suffix': 'summary', 'real_ext': 'ipr',
            'suffix': 'InterPro', 'ext': 'tsv'
        },
        'GO.csv': {
            'display': 'CompleteGOAnnotation',
            'real_suffix': 'summary', 'real_ext': 'go',
            'suffix': 'GO', 'ext': 'csv'
        },
        'GOslim.csv': {
            'display': 'GOSlimAnnotation',
            'real_suffix': 'summary', 'real_ext': 'go_slim',
            'suffix': 'GOslim', 'ext': 'csv'
        },

        # taxonomy result files
        # 'R_RNA_5S_FASTA': { },
        # 'R_RNA_16S_FASTA': { },
        # 'R_RNA_23S_FASTA': { },
        # 'OTU_TABLE': { },
        # 'HDF5_BIOM': { },
        # 'JSON_BIOM': { },
        # 'PRUNED_TREE': { },

    }
}
