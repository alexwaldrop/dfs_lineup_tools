import dfs_optimization_tools.data_import as imp

dk_df = imp.DKResultsImporter("/Users/awaldrop/PycharmProjects/dfs_optimization_tools/data/dfs_results/2019/dk_points_wk3_2019.xlsx")
print(dk_df.data.head())
print(dk_df.data.tail())

fa_df = imp.FFAProjectionsImporter("/Users/awaldrop/PycharmProjects/dfs_optimization_tools/data/projections/2019/ffa_projections_scoring_wk3.csv")
print(fa_df.data.head())


#imp.harmonize_team_names(fa_df.data, dk_df.data)
#imp.harmonize_by_name(fa_df.data, dk_df.data)
data = imp.merge_datasets(fa_df.data, dk_df.data)

data.to_csv("/Users/awaldrop/Desktop/test_week_4_2016.csv", index=False)