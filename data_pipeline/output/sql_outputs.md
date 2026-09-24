## 01_where

```sql
SELECT title, price_gbp, rating FROM books WHERE rating >= 4;
```

| title                                                                                                                                                  |   price_gbp |   rating |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------|------------:|---------:|
| Sharp Objects                                                                                                                                          |       47.82 |        4 |
| Sapiens: A Brief History of Humankind                                                                                                                  |       54.23 |        5 |
| The Dirty Little Secrets of Getting Your Dream Job                                                                                                     |       33.34 |        4 |
| The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics                                                         |       22.6  |        4 |
| Shakespeare's Sonnets                                                                                                                                  |       20.66 |        4 |
| Set Me Free                                                                                                                                            |       17.46 |        5 |
| Scott Pilgrim's Precious Little Life (Scott Pilgrim #1)                                                                                                |       52.29 |        5 |
| Rip it Up and Start Again                                                                                                                              |       35.02 |        5 |
| Chase Me (Paris Nights #2)                                                                                                                             |       25.27 |        5 |
| Black Dust                                                                                                                                             |       34.53 |        5 |
| Worlds Elsewhere: Journeys Around Shakespeareâs Globe                                                                                                                                                        |       40.3  |        5 |
| Wall and Piece                                                                                                                                         |       44.18 |        4 |
| The Four Agreements: A Practical Guide to Personal Freedom                                                                                             |       17.66 |        5 |
| The Elephant Tree                                                                                                                                      |       23.82 |        5 |
| Sophie's World                                                                                                                                         |       15.94 |        5 |
| Behind Closed Doors                                                                                                                                    |       52.22 |        4 |
| Private Paris (Private #10)                                                                                                                            |       47.61 |        5 |
| #HigherSelfie: Wake Up Your Life. Free Your Soul. Find Your Tribe.                                                                                     |       23.11 |        5 |
| We Love You, Charlie Freeman                                                                                                                           |       50.27 |        5 |
| Untitled Collection: Sabbath Poems 2014                                                                                                                |       14.27 |        4 |
| Unseen City: The Majesty of Pigeons, the Discreet Charm of Snails & Other Wonders of the Urban Wilderness                                              |       44.18 |        4 |
| This One Summer                                                                                                                                        |       19.49 |        4 |
| Thirst                                                                                                                                                 |       17.27 |        5 |
| The Past Never Ends                                                                                                                                    |       56.5  |        4 |
| The Nameless City (The Nameless City #1)                                                                                                               |       38.16 |        4 |
| The Most Perfect Thing: Inside (and Outside) a Bird's Egg                                                                                              |       42.96 |        4 |
| The Mindfulness and Acceptance Workbook for Anxiety: A Guide to Breaking Free from Anxiety, Phobias, and Worry Using Acceptance and Commitment Therapy |       23.89 |        4 |
| The Inefficiency Assassin: Time Management Tactics for Working Smarter, Not Longer                                                                     |       20.59 |        5 |
| The Death of Humanity: and the Case for Life                                                                                                           |       58.11 |        4 |
| The Activist's Tao Te Ching: Ancient Advice for a Modern Revolution                                                                                    |       32.24 |        5 |
| Spark Joy: An Illustrated Master Class on the Art of Organizing and Tidying Up                                                                         |       41.83 |        4 |
| Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1)                                                                      |       13.61 |        5 |
| Princess Between Worlds (Wide-Awake Princess #5)                                                                                                       |       13.34 |        5 |
| Outcast, Vol. 1: A Darkness Surrounds Him (Outcast #1)                                                                                                 |       15.44 |        4 |
| Mama Tried: Traditional Italian Cooking for the Screwed, Crude, Vegan, and Tattooed                                                                    |       14.02 |        4 |
| Join                                                                                                                                                   |       35.67 |        5 |
| In the Country We Love: My Family Divided                                                                                                              |       22    |        4 |

## 02_order_limit

```sql
SELECT title, price_inr FROM books ORDER BY price_inr DESC LIMIT 10;
```

| title                                                                                                                           |   price_inr |
|:--------------------------------------------------------------------------------------------------------------------------------|------------:|
| The Death of Humanity: and the Case for Life                                                                                    |     6130.6  |
| Slow States of Collapse: Poems                                                                                                  |     6046.2  |
| Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991                                              |     6039.88 |
| The Past Never Ends                                                                                                             |     5960.75 |
| The Pioneer Woman Cooks: Dinnertime: Comfort Classics, Freezer Food, 16-Minute Meals, and Other Delicious Ways to Solve Supper! |     5951.25 |
| Masks and Shadows                                                                                                               |     5950.2  |
| The Secret of Dreadwillow Carse                                                                                                 |     5921.72 |
| The Electric Pencil: Drawings from Inside State Hospital No. 3                                                                  |     5914.33 |
| Birdsong: A Story in Pictures                                                                                                   |     5764.52 |
| Sapiens: A Brief History of Humankind                                                                                           |     5721.26 |

## 03_distinct

```sql
SELECT DISTINCT category_name FROM categories ORDER BY category_name;
```

| category_name      |
|:-------------------|
| Add a comment      |
| Art                |
| Business           |
| Childrens          |
| Contemporary       |
| Default            |
| Fantasy            |
| Fiction            |
| Food and Drink     |
| Health             |
| Historical Fiction |
| History            |
| Horror             |
| Music              |
| Mystery            |
| New Adult          |
| Nonfiction         |
| Philosophy         |
| Poetry             |
| Politics           |
| Romance            |
| Science            |
| Science Fiction    |
| Self Help          |
| Sequential Art     |
| Spirituality       |
| Thriller           |
| Travel             |
| Young Adult        |

## 04_between

```sql
SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 20 AND 40 ORDER BY price_gbp;
```

| title                                                                                                                                                                           |   price_gbp |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------:|
| The Inefficiency Assassin: Time Management Tactics for Working Smarter, Not Longer                                                                                              |       20.59 |
| Shakespeare's Sonnets                                                                                                                                                           |       20.66 |
| In the Country We Love: My Family Divided                                                                                                                                       |       22    |
| America's Cradle of Quarterbacks: Western Pennsylvania's Football Factory from Johnny Unitas to Joe Montana                                                                     |       22.5  |
| The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics                                                                                  |       22.6  |
| The Requiem Red                                                                                                                                                                 |       22.65 |
| #HigherSelfie: Wake Up Your Life. Free Your Soul. Find Your Tribe.                                                                                                              |       23.11 |
| The Elephant Tree                                                                                                                                                               |       23.82 |
| Olio                                                                                                                                                                            |       23.88 |
| The Mindfulness and Acceptance Workbook for Anxiety: A Guide to Breaking Free from Anxiety, Phobias, and Worry Using Acceptance and Commitment Therapy                          |       23.89 |
| Saga, Volume 6 (Saga (Collected Editions) #6)                                                                                                                                   |       25.02 |
| Chase Me (Paris Nights #2)                                                                                                                                                      |       25.27 |
| Unbound: How Eight Technologies Made Us Human, Transformed Society, and Brought Our World to the Brink                                                                          |       25.52 |
| Reasons to Stay Alive                                                                                                                                                           |       26.41 |
| Foolproof Preserving: A Guide to Small Batch Jams, Jellies, Pickles, Condiments, and More: A Foolproof Guide to Making Small Batch Jams, Jellies, Pickles, Condiments, and More |       30.52 |
| The Five Love Languages: How to Express Heartfelt Commitment to Your Mate                                                                                                       |       31.05 |
| Throwing Rocks at the Google Bus: How Growth Became the Enemy of Prosperity                                                                                                     |       31.12 |
| When We Collided                                                                                                                                                                |       31.77 |
| The Activist's Tao Te Ching: Ancient Advice for a Modern Revolution                                                                                                             |       32.24 |
| Penny Maybe                                                                                                                                                                     |       33.29 |
| The Dirty Little Secrets of Getting Your Dream Job                                                                                                                              |       33.34 |
| My Paris Kitchen: Recipes and Stories                                                                                                                                           |       33.37 |
| You can't bury them all: Poems                                                                                                                                                  |       33.63 |
| Black Dust                                                                                                                                                                      |       34.53 |
| Rip it Up and Start Again                                                                                                                                                       |       35.02 |
| Join                                                                                                                                                                            |       35.67 |
| Political Suicide: Missteps, Peccadilloes, Bad Calls, Backroom Hijinx, Sordid Pasts, Rotten Breaks, and Just Plain Dumb Mistakes in the Annals of American Politics             |       36.28 |
| The Bear and the Piano                                                                                                                                                          |       36.89 |
| The Gutsy Girl: Escapades for Your Life of Epic Adventure                                                                                                                       |       37.13 |
| How Music Works                                                                                                                                                                 |       37.32 |
| Mesaerion: The Best Science Fiction Stories 1800-1849                                                                                                                           |       37.59 |
| The Nameless City (The Nameless City #1)                                                                                                                                        |       38.16 |
| Security                                                                                                                                                                        |       39.25 |
| Soul Reader                                                                                                                                                                     |       39.58 |

## 05_join

```sql
SELECT c.category_name, b.title, b.rating, b.price_inr FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY b.rating DESC, c.category_name, b.title LIMIT 20;
```

| category_name   | title                                                                                                                                                  |   rating |   price_inr |
|:----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------|---------:|------------:|
| Default         | The Inefficiency Assassin: Time Management Tactics for Working Smarter, Not Longer                                                                     |        5 |     2172.24 |
| Fantasy         | Princess Between Worlds (Wide-Awake Princess #5)                                                                                                       |        5 |     1407.37 |
| Fiction         | Private Paris (Private #10)                                                                                                                            |        5 |     5022.85 |
| Fiction         | Thirst                                                                                                                                                 |        5 |     1821.98 |
| Fiction         | We Love You, Charlie Freeman                                                                                                                           |        5 |     5303.48 |
| History         | Sapiens: A Brief History of Humankind                                                                                                                  |        5 |     5721.26 |
| Music           | Rip it Up and Start Again                                                                                                                              |        5 |     3694.61 |
| Nonfiction      | #HigherSelfie: Wake Up Your Life. Free Your Soul. Find Your Tribe.                                                                                     |        5 |     2438.1  |
| Nonfiction      | Worlds Elsewhere: Journeys Around Shakespeareâs Globe                                                                                                                                                        |        5 |     4251.65 |
| Philosophy      | Sophie's World                                                                                                                                         |        5 |     1681.67 |
| Romance         | Black Dust                                                                                                                                             |        5 |     3642.92 |
| Romance         | Chase Me (Paris Nights #2)                                                                                                                             |        5 |     2665.98 |
| Science Fiction | Join                                                                                                                                                   |        5 |     3763.19 |
| Sequential Art  | Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1)                                                                      |        5 |     1435.86 |
| Sequential Art  | Scott Pilgrim's Precious Little Life (Scott Pilgrim #1)                                                                                                |        5 |     5516.6  |
| Spirituality    | The Activist's Tao Te Ching: Ancient Advice for a Modern Revolution                                                                                    |        5 |     3401.32 |
| Spirituality    | The Four Agreements: A Practical Guide to Personal Freedom                                                                                             |        5 |     1863.13 |
| Thriller        | The Elephant Tree                                                                                                                                      |        5 |     2513.01 |
| Young Adult     | Set Me Free                                                                                                                                            |        5 |     1842.03 |
| Add a comment   | The Mindfulness and Acceptance Workbook for Anxiety: A Guide to Breaking Free from Anxiety, Phobias, and Worry Using Acceptance and Commitment Therapy |        4 |     2520.4  |

