def flatten_dictionary(dct: dict) -> dict:
    """
    It takes a dictionary, and returns a dictionary with all the nested dictionaries flattened

    :param dct: dict
    :type dct: dict
    :return: A dictionary with the keys being the path to the value and the value being the value.
    """
    result = dict()

    for key, value in dct.items():
        if isinstance(value, dict) and key != "hours":
            part_result = flatten_dictionary(value)
            result.update(part_result)
        else:
            result[key] = value

    return result


if __name__ == '__main__':
    ordbog = {'name': 'Abby Rappoport, LAC, CMQ', 'address': '1616 Chapala St, Ste 2', 'city': 'Santa Barbara',
              'state': 'CA', 'postal_code': '93101', 'latitude': 34.4266787, 'longitude': -119.7111968, 'stars': 5.0,
              'review_count': 7, 'is_open': 0,
              'attributes': {'BikeParking': 'True', 'BusinessAcceptsCreditCards': 'True', 'RestaurantsPriceRange2': '2',
                             'CoatCheck': 'False', 'RestaurantsTakeOut': 'False', 'RestaurantsDelivery': 'False',
                             'Caters': 'False', 'WiFi': "u'no'",
                             'BusinessParking': "{'garage': False, 'street': False, 'validated': False, 'lot': True, 'valet': False}",
                             'WheelchairAccessible': 'True', 'HappyHour': 'False', 'OutdoorSeating': 'False',
                             'HasTV': 'False', 'RestaurantsReservations': 'False', 'DogsAllowed': 'False',
                             'ByAppointmentOnly': 'False'},
              'categories': 'Department Stores, Shopping, Fashion, Home & Garden, Electronics, Furniture Stores',
              'hours': {'Monday': '8:0-22:0', 'Tuesday': '8:0-22:0', 'Wednesday': '8:0-22:0', 'Thursday': '8:0-22:0',
                        'Friday': '8:0-23:0', 'Saturday': '8:0-23:0', 'Sunday': '8:0-22:0'}}

    # print(ordbog["atributes"])
    #
    print(flatten_dictionary(ordbog))
