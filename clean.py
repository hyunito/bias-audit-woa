import pandas as pd 
from sample import test_data

#I only included these cleaning processes: convert to right data type, data validation (age only), handle missing values, handle inconsistent format, remove duplicates

#I used the possible values based sa adult_data.csv
    #age -> 0 to 120 (but in dataset there are only records of 17-90)
    #sex -> male, female
    #race -> amer-indian-eskimo, asian-pac-islander, black, white, other
    #marital-status -> divorced, married-AF-spouse, married-civ-spouse, married-spouse-absent, never-married, separated, widowed
  
#I separated each into functions per attribute

df = pd.DataFrame(test_data)


def clean_demographics(df):
    df = df.copy()

#---Age Cleaning---
    def age_cleaning(df):
        df = df.copy()
    #Converting to right data type
        df['age'] = pd.to_numeric(df['age'], errors = 'coerce').astype('Int64')
    #Handle missing values (fill it with median)
        df['age'] = df['age'].fillna(df['age'].median())
    #Data Validation (only age 0-120)
        df = df[(df['age'] >= 0) & (df['age'] <= 120)]
        return df


#---Sex Cleaning---
    def sex_cleaning(df):
        df = df.copy()
    #Convert to right data type, remove space, standardize format 
        df['sex'] = df['sex'].astype(str).str.strip().str.lower()
    #Fix inconsistent labels
        sex_map = {
            'm': 'Male',
            'male': 'Male',
            'f': 'Female',
            'female': 'Female'
        }
    #Handle other values / missing values
        df['sex'] = df['sex'].map(sex_map).fillna('unknown')
        return df


#---Race Cleaning---
    def race_cleaning(df):
        df = df.copy()
    #Convert to string, remove space, fix capitalization 
        df['race'] = df['race'].astype(str).str.strip().str.lower()       
    #Convert to right label (similar to IN(%word%) of SQL)
        df.loc[df['race'].str.contains('amer'), 'race'] = 'amer-indian-eskimo'
        df.loc[df['race'].str.contains('indian'), 'race'] = 'amer-indian-eskimo'
        df.loc[df['race'].str.contains('eskimo'), 'race'] = 'amer-indian-eskimo'
        df.loc[df['race'].str.contains('asian'), 'race'] = 'asian-pac-islander'
        df.loc[df['race'].str.contains('pac'), 'race'] = 'asian-pac-islander'
        df.loc[df['race'].str.contains('islander'), 'race'] = 'asian-pac-islander'
    #Fix inconsistent labels
        race_map = {
            'amer-indian-eskimo': 'Amer-Indian-Eskimo',
            'asian-pac-islander': 'Asian-Pac-Islander',
            'black': 'Black',
            'white': 'White'
        }
    #Handle other values / missing values
        df['race'] = df['race'].map(race_map).fillna('Other')
        return df


#---Marital Status Cleaning---
    def marital_cleaning(df):
        df = df.copy()
    #Convert to string, remove space, fix capitalization
        df['marital-status'] = df['marital-status'].astype(str).str.strip().str.lower()
    #Convert to right label (similar to IN(%word%) of SQL)
        df.loc[df['marital-status'].str.contains('af'), 'marital-status'] = 'married-af-spouse'
        df.loc[df['marital-status'].str.contains('civ'), 'marital-status'] = 'married-civ-spouse'
        df.loc[df['marital-status'].str.contains('absent'), 'marital-status'] = 'married-spouse-absent'
        df.loc[df['marital-status'].str.contains('never'), 'marital-status'] = 'never-married'
    #Fix inconsistent labels
        marital_map = {
            'divorced': 'Divorced',  
            'married-af-spouse': 'Married-AF-spouse',
            'married-civ-spouse': 'Married-civ-spouse',
            'married-spouse-absent': 'Married-spouse-absent',
            'never-married': 'Never-married',
            'separated': 'Separated',
            'widowed': 'Widowed'
        }
    #Handle other values / missing values
        df['marital-status'] = df['marital-status'].map(marital_map).fillna('unknown')
        return df

#---Removing Duplicate Records---
    def remove_duplicate(df):
        df = df.copy()
        df = df.drop_duplicates()
        return df
    

    df = age_cleaning(df)
    df = sex_cleaning(df)
    df = race_cleaning(df)
    df = marital_cleaning(df)
    df = remove_duplicate(df)

    return df


print("\nOriginal dataset:")
print(df)

print("\nCleaned dataset:")
clean_df = clean_demographics(df)
print(clean_df)
