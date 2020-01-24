---
date: '2020-01-23'
filename: 2020-01-23-computing-longest-consecutive.md
tags:
- datascience
- pandas
- python
title: Computing longest consecutive sequence of values matching a condition

---

On [StackOverflow][], user [DSM][] suggests that given a series `y`, you can find the longest sequence of consecutive items matching a condition by first creating a boolean series that is `True` (or `1`) for items that match the condition (and `False` or `0` otherwise), and then running:

```
result = y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1)
```

There's a reasonable explanation in the answer, but I'm new enough to Pandas that I wanted to work it out for myself.

[stackoverflow]: https://stackoverflow.com/questions/27626542/counting-consecutive-positive-value-in-python-array
[dsm]: https://stackoverflow.com/users/487339/dsm

## The magic

```=import_pandas
import pandas
```

```=sample_data
data = [
  ['2018-01-01', 13],
  ['2018-01-02', 19],
  ['2018-01-03', 29],
  ['2018-01-04', 30],
  ['2018-01-05', 24],
  ['2018-01-06', 12],
  ['2018-01-07', 17],
  ['2018-01-08', 35],
  ['2018-01-09', 43],
  ['2018-01-10', 36],
  ['2018-01-11', 51],
  ['2018-01-12', 60],
  ['2018-01-13', 61],
  ['2018-01-14', 23],
  ['2018-01-15', 21],
  ['2018-01-16', 33],
  ['2018-01-17', 34],
  ['2018-01-18', 32],
  ['2018-01-19', 34],
  ['2018-01-20', 47],
  ['2018-01-21', 49],
  ['2018-01-22', 39],
  ['2018-01-23', 55],
  ['2018-01-24', 42],
  ['2018-01-25', 30],
  ['2018-01-26', 34],
  ['2018-01-27', 53],
  ['2018-01-28', 52],
  ['2018-01-29', 43],
  ['2018-01-30', 31],
  ['2018-01-31', 30],
  ]

data_unzipped = list(zip(*data))
df = pandas.DataFrame({'DATE': data_unzipped[0], 'TMAX': data_unzipped[1]})
```

```=df_to_table --hide
import tabulate
def df_to_table(df, filename):
  print('writing', filename, '...')
  with open(filename, 'w') as fd:
    fd.write(tabulate.tabulate(df, headers=df.columns, tablefmt='github'))
```

```=write_initial --hide
df_to_table(df, 'initial.txt')
```

<!-- include initial.txt -->

### Step 1

Create a boolean column indicating whether or not the temperature is below freezing:

```=step1
df['freezing'] = df['TMAX'] <= 32
```

```=write_step1 --hide
df_to_table(df, 'step1.txt')
```

<!-- include step1.txt -->

### Step 2

```=step2
df['step2'] = df['freezing'] != df['freezing'].shift()
```

```=write_step2 --hide
df_to_table(df, 'step2.txt')
```

<!-- include step2.txt -->

### Step 3

```=step3
df['step3'] = df['step2'].cumsum()
```

```=write_step3 --hide
df_to_table(df, 'step3.txt')
```

<!-- include step3.txt -->

### Step 4

```=step4
df['step4'] = df['freezing'].groupby(df['step3']).cumcount() + 1
```

```=write_step4 --hide
df_to_table(df, 'step4.txt')
```

<!-- include step4.txt -->

### Step 5

```=step5
df['step5'] = df['freezing'] * df['step4']
```

```=write_step5 --hide
df_to_table(df, 'step5.txt')
```

<!-- include step5.txt -->

### Step 6

```=get_max_dbf
max_consecutive_dbf = df['step5'].max()
```

And if everything worked as expected, we should find that the longest consecutive sequence of days on which the temperature stayed below freezing was 7 days, from 2018-01-01 through 2018-01-07:

```=check_answer
assert max_consecutive_dbf == 7
```

```=sample.py --file --hide
<<import_pandas>>
<<df_to_table>>
<<sample_data>>
<<write_initial>>
<<step1>>
<<write_step1>>
<<step2>>
<<write_step2>>
<<step3>>
<<write_step3>>
<<step4>>
<<write_step4>>
<<step5>>
<<write_step5>>
<<get_max_dbf>>
<<check_answer>>
```


[daily summaries]: https://www.ncdc.noaa.gov/cdo-web/search?datasetid=GHCND
[pandas]: https://pandas.pydata.org
[27626542]: https://stackoverflow.com/questions/27626542/counting-consecutive-positive-value-in-python-array

