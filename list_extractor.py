import re
import requests
import json
import pandas as pd

event_id = "0cHKxAxJm3"

"""
https://pnnct8s9sk.execute-api.us-east-1.amazonaws.com/prod/players?limit=100&eventId=o6QVSixlGK&expand[]=army&expand[true]=subFaction&expand[true]=character&expand[]=team&expand[]=user
https://pnnct8s9sk.execute-api.us-east-1.amazonaws.com/prod/armylists/5D9XU4YP2V
"""

tsn_query = """
{
  "version": "1.0.0",
  "queries": [
    {
      "Query": {
        "Commands": [
          {
            "SemanticQueryDataShapeCommand": {
              "Query": {
                "Version": 2,
                "From": [
                  {
                    "Name": "f",
                    "Entity": "Faction Outcomes",
                    "Type": 0
                  },
                  {
                    "Name": "t",
                    "Entity": "Tournament Dates",
                    "Type": 0
                  }
                ],
                "Select": [
                  {
                    "Column": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "f"
                        }
                      },
                      "Property": "Tournament Name"
                    },
                    "Name": "Faction Outcomes.Tournament Name"
                  },
                  {
                    "Column": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "f"
                        }
                      },
                      "Property": "Outcome"
                    },
                    "Name": "Faction Outcomes.Outcome"
                  },
                  {
                    "Column": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "f"
                        }
                      },
                      "Property": "Tournament Tier"
                    },
                    "Name": "Faction Outcomes.Tournament Tier"
                  },
                  {
                    "Aggregation": {
                      "Expression": {
                        "Column": {
                          "Expression": {
                            "SourceRef": {
                              "Source": "f"
                            }
                          },
                          "Property": "Points (Total)"
                        }
                      },
                      "Function": 0
                    },
                    "Name": "Sum(Faction Outcomes.Points (Total))"
                  },
                  {
                    "Column": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "f"
                        }
                      },
                      "Property": "Faction: Subfaction"
                    },
                    "Name": "Faction Outcomes.Faction: Subfaction"
                  },
                  {
                    "Column": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "t"
                        }
                      },
                      "Property": "Country (ABV)"
                    },
                    "Name": "Tournament Dates.Country (ABV)"
                  }
                ],
                "Where": [
                  {
                    "Condition": {
                      "In": {
                        "Expressions": [
                          {
                            "Column": {
                              "Expression": {
                                "SourceRef": {
                                  "Source": "f"
                                }
                              },
                              "Property": "Player"
                            }
                          }
                        ],
                        "Values": [
                          [
                            {
                              "Literal": {
                                "Value": "'last_name, first_name'"
                              }
                            }
                          ]
                        ]
                      }
                    }
                  },
                  {
                    "Condition": {
                      "In": {
                        "Expressions": [
                          {
                            "Column": {
                              "Expression": {
                                "SourceRef": {
                                  "Source": "f"
                                }
                              },
                              "Property": "Season"
                            }
                          }
                        ],
                        "Values": [
                          [
                            {
                              "Literal": {
                                "Value": "'Season 2'"
                              }
                            }
                          ]
                        ]
                      }
                    }
                  },
                  {
                    "Condition": {
                      "Not": {
                        "Expression": {
                          "In": {
                            "Expressions": [
                              {
                                "Column": {
                                  "Expression": {
                                    "SourceRef": {
                                      "Source": "t"
                                    }
                                  },
                                  "Property": "Version"
                                }
                              }
                            ],
                            "Values": [
                              [
                                {
                                  "Literal": {
                                    "Value": "null"
                                  }
                                }
                              ]
                            ]
                          }
                        }
                      }
                    }
                  }
                ],
                "OrderBy": [
                  {
                    "Direction": 2,
                    "Expression": {
                      "Column": {
                        "Expression": {
                          "SourceRef": {
                            "Source": "f"
                          }
                        },
                        "Property": "Outcome"
                      }
                    }
                  }
                ]
              },
              "Binding": {
                "Primary": {
                  "Groupings": [
                    {
                      "Projections": [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5
                      ]
                    }
                  ]
                },
                "DataReduction": {
                  "DataVolume": 3,
                  "Primary": {
                    "Window": {
                      "Count": 500
                    }
                  }
                },
                "Version": 1
              },
              "ExecutionMetricsKind": 1
            }
          }
        ]
      },
      "QueryId": "",
      "ApplicationContext": {
        "DatasetId": "0cdc51d2-4b8b-440b-a490-6ecf3db13e5e",
        "Sources": [
          {
            "ReportId": "09893c93-2eda-46f1-b96e-1f7514f2015c",
            "VisualId": "2bb65e3200a719060e34"
          }
        ]
      }
    }
  ],
  "cancelQueries": [],
  "modelId": 89938
}
"""

tsn_headers = {
    'X-PowerBI-ResourceKey': '71728b61-4f5a-402a-9000-6457d14f4879',
}
tsn_url = "https://wabi-uk-south-c-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"

fetch_event_lists_url = f"https://pnnct8s9sk.execute-api.us-east-1.amazonaws.com/prod/players?limit=100&eventId={{event_id}}&expand[true]=army&expand[true]=subFaction&expand[true]=character&expand[]=team&expand[]=user"

fetch_list_text_url = f"https://pnnct8s9sk.execute-api.us-east-1.amazonaws.com/prod/armylists/{{list_id}}"
headers = {
    'Authorization': 'Bearer eyJraWQiOiJjd1VSK1F4KzdLb1hmdWlFK0hudjFBTTVXS2ppck9peFJVdEY2NDFpazA4PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OTBjZGM0ZC1jMDEzLTQ5ZDctYjI1MS1jY2I1ZTY1ZTdkNGMiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9XbGt2b21nZGUiLCJjdXN0b206aXNKdWRnZSI6ImZhbHNlIiwiY3VzdG9tOmlzT3JnYW5pemVyIjoiZmFsc2UiLCJzdG9yZVVzZXIiOiJmYWxzZSIsImN1c3RvbTpzdG9yZVVzZXIiOiJmYWxzZSIsImF1dGhfdGltZSI6MTY3MDIzMDI2Niwibmlja25hbWUiOiJQYXVsIiwiZXhwIjoxNjgyNjcxODIwLCJpYXQiOjE2ODI1ODU0MjAsImVtYWlsIjoicHVjaWVrQGdtYWlsLmNvbSIsInN1YnNjcmliZXIiOiJmYWxzZSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJjb2duaXRvOnVzZXJuYW1lIjoicHVjaWVrQGdtYWlsLmNvbSIsImlzQWRtaW4iOiJmYWxzZSIsImN1c3RvbTpzdWJzY3JpYmVyIjoiZmFsc2UiLCJnaXZlbl9uYW1lIjoiVHltb3RldXN6IiwidXNlcklkIjoiaWlVRHhBQ1hUUCIsImlzVGVzdGVyIjoiZmFsc2UiLCJjdXN0b206dXNlcklkIjoiaWlVRHhBQ1hUUCIsImF1ZCI6IjZhdmZyaTZ2OXRnZmU2Zm9udWpxMDdldTljIiwiaXNPcmdhbml6ZXIiOiJmYWxzZSIsImV2ZW50X2lkIjoiOGUyNjM0NDctNjg5Ni00NTgxLTkxMTYtMGIwYjQ3NzhhYjBlIiwidG9rZW5fdXNlIjoiaWQiLCJpc0p1ZGdlIjoiZmFsc2UiLCJmYW1pbHlfbmFtZSI6IlBhdWwifQ.bciuKyn9X7bIoORi8gb6jD0d79QWsbQX_xaIvsdr_aG7X32k-QsEXOF1dfQy770KeSiFjOpk001fEJBF0Mcfey27RsOoFHye4XFDvvE-lf8EPzYSnYlRZAeQeN98Ar3BL5bIh-a0bm3WDwD_nN2qpP7qzhU0km-PKCD4voEaKqyjA1jOpGFRl5z8aD7kISKV7fM2KGEbZ0c_7vPWwzEchaq6ciHVhyO05SExDapIPBqedwXoCqJ24hWcSbFHbPXuSZ0N6kbGJRDNkRM0zTVB_98q9oI23bGhvKTjkEu0td1OM3EgQaCQ4cToT7Tm-mtH3QxeHUhc0mE6DS4Xih-49A'
}

lists_response_json = requests.get(fetch_event_lists_url.format(event_id=event_id), headers=headers).json()

players = []

for player in lists_response_json["data"]:
    enriched_player = {}
    enriched_player["first_name"] = player["user"]["firstName"]
    enriched_player["last_name"] = player["user"]["lastName"]
    try:
        enriched_player["list_id"] = player["armyListObjectId"]
    except KeyError:
        enriched_player["list_id"] = None
    if enriched_player["list_id"]:
        try:
            enriched_player["list"] = requests.get(fetch_list_text_url.format(list_id=enriched_player["list_id"]),
                                               headers=headers).json()["armyListText"].replace('\n', '<br />')
        except KeyError:
            enriched_player["list"] = None
    else:
        enriched_player["list"] = None
    try:
        enriched_player["faction"] = player["army"]["name"]
    except KeyError:
        enriched_player["faction"] = None

    enriched_player["events"] = []
    parsed_tsn_query = tsn_query.replace("first_name", player["user"]["firstName"])
    parsed_tsn_query = parsed_tsn_query.replace("last_name", player["user"]["lastName"])
    tsn_data = requests.post(tsn_url, headers=tsn_headers, data=parsed_tsn_query).json()
    if "ValueDicts" in tsn_data['results'][0]['result']['data']['dsr']['DS'][0]:
        events_root = tsn_data['results'][0]['result']['data']['dsr']['DS'][0]['ValueDicts']
        iter = 0
        last_result = None
        if len(events_root['D0']) != len(events_root['D1']):
            events_root['D1'].insert(0, events_root['D1'][0])
        for event in events_root['D0']:
            try:
                last_result = events_root['D1'][iter]
            except IndexError:
                pass
            event_string = "%s: %s" % (event, last_result)
            iter += 1
            enriched_player["events"].append(event_string)
    players.append(enriched_player)

players.sort(key=lambda x: x["last_name"])
# Save the dictionary as html table
with open("players.html", "w", encoding='UTF-8') as f:
    f.write("<table border=1 align=top valign=top>")
    f.write("<tr>")
    f.write("<th>Name</th>")
    f.write("<th>Faction</th>")
    f.write("<th>Events</th>")
    f.write("<th>List</th>")
    f.write("</tr>")
    for player in players:
        f.write("<tr>")
        f.write("<td>%s %s</td>" % (player["first_name"], player["last_name"]))
        f.write("<td>%s</td>" % player["faction"])
        f.write("<td>%s</td>" % "<br />".join(player["events"]))
        f.write("<td>%s</td>" % player["list"])
        f.write("</tr>")
    f.write("</table>")

