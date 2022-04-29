# Product Team

[![Build Status](https://github.com/Tproducts/products/workflows/TDD%20Tests/badge.svg)](https://github.com/Tproducts/products/actions)
[![Build Status](https://github.com/Tproducts/products/workflows/BDD%20Tests/badge.svg)](https://github.com/Tproducts/products/actions)
[![codecov.io](https://codecov.io/github/Tproducts/products/coverage.svg?branch=main)](https://codecov.io/github/Tproducts/products?branch=main)
![](https://img.shields.io/badge/language-Python-green.svg)
[![Open in Remote - Containers](https://img.shields.io/static/v1?label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://nyu-product-service-sp2203.us-south.cf.appdomain.cloud/)

## The Roles of our Scrum team

- Product Owner : Jingzhou Wang
- Scrum Master : Taowei Xia
- Development Team: Yujie Fan, Yuejiang Wu, Qiqi Liang

## Daily Standup

Hints: checkout the detail in chapter 3 ppt

### skeleton about daily standup

- Occurs every day at the same time and place
- Called a "standup" because everyone should remain standing during the meeting to keep it short
  - Timeboxed to 15 minutes
  - Not a project status meeting — all status should be tabled for later discussion
- Each team member briefly reports on their work

### Daily Standup Question

- Each team member answers three questions:
  - What did I accomplish the previous day?
  - What will I work on today?
  - What blockers or impediments are in my way?

### Daily Execution

- Take the next highest priority item from the Sprint Backlog
- Assign it to yourself
- Start working on it
- No one should have more than one story assigned to them unless they are blocked and want to start a second story while waiting
- When you are finished, move the Story to the Done column

## The main skeleton of product service

TDD test cases can be ran with:

```
nosetests
```
The code coverage rate can achieve 95%

Unit test can be ran with:

```
python -m unittest discover
```

App running:

```
// method 1
flask run
// method 2
honcho start
```

All Available Routers check:

```
flask routes
```
