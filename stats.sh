#!bin/bash

# Print number of actions by day.
sql="\
   SELECT strftime('%Y-%m-%d', run_at) d, action, count(count) \
     FROM osiris \
 GROUP BY d, action \
"

sqlite3 statistics.db "${sql};"
