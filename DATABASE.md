### users
| データ名     | データ型    | 主キー | 外部キー |
| -------- | ------- | --- | ---- |
| id       | INT     | ○   |      |
| username | VARCHAR |     |      |
| password | VARCHAR |     |      |

### groups
| データ名          | データ型    | 主キー | 外部キー     |
| ------------- | ------- | --- | -------- |
| id            | INT     | ○   |          |
| group_name    | VARCHAR |     |          |
| owner_user_id | INT     |     | users.id |

### UserGroup
| データ名     | データ型    | 主キー | 外部キー      |
| -------- | ------- | --- | --------- |
| id       | INT     | ○   |           |
| user_id  | INT     |     | users.id  |
| group_id | INT     |     | groups.id |
| points   | INT     |     |           |
| is_host  | BOOLEAN |     |           |

### shops
| データ名        | データ型    | 主キー | 外部キー      |
| ----------- | ------- | --- | --------- |
| id          | INT     | ○   |           |
| group_id    | INT     |     | groups.id |
| reward_name | VARCHAR |     |           |
| cost        | INT     |     |           |
| description | TEXT    |     |           |

### quests
| データ名        | データ型     | 主キー | 外部キー      |
| ----------- | -------- | --- | --------- |
| id          | INT      | ○   |           |
| group_id    | INT      |     | groups.id |
| quest_name  | VARCHAR  |     |           |
| description | TEXT     |     |           |
| start_time  | DATETIME |     |           |
| end_time    | DATETIME |     |           |
