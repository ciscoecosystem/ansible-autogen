# ACI Gen

This project is used to generate models and resources for different products which include ansible, terraform and more.


## HOW to install

We are using `pipenv` to manage dependencies on this project

### Install on MACOS

```
brew install pipenv
```

### Other OSes

https://docs.pipenv.org/install/#installing-pipenv

# HOW to use

- Run `pipenv sync` to install the deps
- Just run `pipenv shell` in the current folder and then run `python ansible_generator.py <class_name>`

