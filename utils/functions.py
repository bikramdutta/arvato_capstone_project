import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from tqdm.auto import tqdm, trange

tqdm.pandas()


def reduce_mem_usage(df):
    start_mem_usg = df.memory_usage().sum() / 1024 ** 2

    print("Memory usage of dataframe: ", start_mem_usg, " MB")

    na_list = []  # Keeps track of columns that have missing values filled in.
    for col in tqdm(df.columns):
        if df[col].dtype != object:  # Exclude strings

            # make variables for Int, max and min
            is_int = False
            mx = df[col].max()
            mn = df[col].min()

            # Integer does not support NA, therefore, NA needs to be filled
            if not np.isfinite(df[col]).all():
                na_list.append(col)
                df[col].fillna(mn - 1, inplace=True)

                # test if column can be converted to an integer
            asint = df[col].fillna(0).astype(np.int64)
            result = (df[col] - asint)
            result = result.sum()
            if -0.01 < result < 0.01:
                is_int = True

            # Make Integer/unsigned Integer datatypes
            if is_int:
                if mn >= 0:
                    if mx < 255:
                        df[col] = df[col].astype(np.uint8)
                    elif mx < 65535:
                        df[col] = df[col].astype(np.uint16)
                    elif mx < 4294967295:
                        df[col] = df[col].astype(np.uint32)
                    else:
                        df[col] = df[col].astype(np.uint64)
                else:
                    if mn > np.iinfo(np.int8).min and mx < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif mn > np.iinfo(np.int16).min and mx < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif mn > np.iinfo(np.int32).min and mx < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                    elif mn > np.iinfo(np.int64).min and mx < np.iinfo(np.int64).max:
                        df[col] = df[col].astype(np.int64)

                        # Make float datatypes 32 bit
            else:
                df[col] = df[col].astype(np.float32)

    # Print final result
    print("___MEMORY USAGE AFTER COMPLETION:___")
    mem_usg = df.memory_usage().sum() / 1024 ** 2
    print(f'Memory usage is: {mem_usg} MB')
    print(f'This is {100 * mem_usg / start_mem_usg:.2f}% of the initial size')

    return df, na_list


def map_nans(value, mapping):
    try:
        mapped_value = int(value)
    except:
        mapped_value = value

    try:
        if np.isnan(value):
            mapped_value = -99999
    except:
        pass

    if str(mapped_value) in mapping:
        mapped_value = -99999

    return mapped_value


def replace_missing_or_unknown(df, feat_info):
    # map_dict = {}
    # parse_string_dict = lambda s: map_dict.fromkeys(s.strip('[]').split(','), np.nan)
    parse_string_list = lambda s: s.strip('[]').split(',')

    for _, row in feat_info[feat_info['missing_or_unknown'] != '[]'].iterrows():
        column = row['attribute']

        missing_or_unknown = parse_string_list(row['missing_or_unknown'])
        tqdm.write(f'Processing {column}')
        df[column] = df[column].progress_apply(map_nans, args=(missing_or_unknown,))
        df[column] = df[column].replace({-99999: np.nan})

    return df


def nans_count(df, axis=0):
    nans_number = pd.DataFrame(df.isnull().sum(axis=axis) * 100 / df.shape[axis], columns=['nan_count'])
    return nans_number[nans_number['nan_count'] > 0]


def unique_values(df):
    for column in tqdm(df.columns):
        values = list(df[column].unique())
        print(f'{column}: {values}')


# Compare the distribution of values for at least five columns where there are
# no or few missing values, between the two subsets.

def compare_distributions(few_nans, lots_nans, columns, threshold):
    fig, axes = plt.subplots(nrows=len(columns), ncols=2, figsize=(15, 3 * len(columns)),
                             gridspec_kw={'hspace': 0.5, 'wspace': 0.5})
    fig.subplots_adjust(top=0.97)
    fig.suptitle('Distribution of values from columns with no values')

    for idx, column in tqdm(enumerate(columns)):
        if column != 'LNR':
            ax1 = sns.countplot(x=column, data=few_nans, ax=axes[idx, 0])
            ax1.set(title=f'<={threshold}% missing values per row')
            ax2 = sns.countplot(x=column, data=lots_nans, ax=axes[idx, 1])
            ax2.set(title=f'>{threshold}% missing values per row')

    plt.show()
    return fig
