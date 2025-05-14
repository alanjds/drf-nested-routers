# Changelog

## 0.94.2
_May 14, 2025_

* Added tests for Django 5.1 and Python 3.13.
* Removed tests for Django 4.1, Python 3.8 and DRF 3.13
* Added support for `use_regex_path=False` in DRF 3.15 (@Gibsondz on PR#355)

## 0.94.1
_May 10, 2024_

* Removed support for Django 3.2 LTS.
* Changed minimum requirements (Python 3.8, Django 4.2, DRF 3.14)
* Add type hints

## 0.94.0
_May 10, 2024_

* Add initial type hint support
* Removed Python 2 compatibility
* Changed CI from Travis to GitHub CI
* Updated timezone database

## 0.93.5
_Dec 19, 2023_

* Add Support for Django 4.x
* Removed support for Python 3.6, Django 1.11 and DRF 3.6
* Change minimum requirements (Python 3.7, Django 3.2, DRF 3.14.0)
* Update timezone database
* Add swagger support for NestedViewSetMixin

## 0.93.4
_Oct 15, 2021_

* Add serializer examples
* Fix KeyError exception for nested resource during generate swagger ( #228 )
* Improved documentation

