from random import randint
import xml.sax
import xml.dom.minidom
import datetime as dt


class TrainSchedule:

    def __init__(self) -> None:
        self._train_schedule: dict = {}
        self._ids: set = set()

    @property
    def train_schedule(self) -> dict:
        return self._train_schedule

    def add_element(self, train_number: str, departure_station: str, arrival_station: str,
                    departure_time: dt.datetime, arrival_time: dt.datetime):
        """Add element to dict."""
        if len(self._ids) >= 1000:
            raise "You can't add more then 1000 elements to table."
        new_id: str = str(randint(0, 1000))
        while new_id in self._ids:
            new_id = str(randint(0, 1000))
        self._ids.add(new_id)
        self._train_schedule[new_id] = {
            "number": train_number,
            "departure station": departure_station,
            "arrival station": arrival_station,
            "departure time": departure_time,
            "arrival time": arrival_time,
            "travel time": arrival_time - departure_time
        }

    def find_elements(self, filters: tuple | list, find_mode: str) -> dict | None:
        """Find elements in train schedule and return
        dict with these elements or None."""
        print("Parser", filters, find_mode)
        result: dict = {}
        format_string = "%Y-%m-%d %H:%M:%S"
        for key, value in self._train_schedule.items():
            match find_mode:
                case "ND":
                    if filters[0] == value["number"] or filters[1] == value["departure time"]:
                        result[key] = self._train_schedule[key]
                        continue
                case "DA":
                    print(filters)
                    print("departure", value["departure time"].date(), "arrival", value["arrival time"].date())
                    if filters[0]:
                        if filters[0][0] <= value["departure time"].date() <= filters[0][1]:
                            result[key] = self._train_schedule[key]
                            continue
                    elif filters[1]:
                        if filters[1][0] <= value["arrival time"].date() <= filters[1][0]:
                            result[key] = self._train_schedule[key]
                            continue
                case "DAS":
                    if filters[0] == value["departure station"] or filters[1] == value["arrival station"]:
                        result[key] = self._train_schedule[key]
                        continue
                case "TT":
                    if filters[0] and filters[1]:
                        try:
                            input_travel_time = dt.datetime.strptime(f"00-00-{filters[0]} {filters[1]}",
                                                                     format_string) - \
                                                dt.datetime.strptime("00-00-00 00:00:00", format_string)
                        except ValueError as err:
                            print(err)
                            continue
                        if value["travel time"] <= input_travel_time:
                            result[key] = self._train_schedule[key]
                            continue
                    elif filters[1]:
                        input_travel_time = dt.datetime.strptime(f"00-00-00 {filters[1]}", format_string) - \
                                            dt.datetime.strptime("00-00-00 00:00:00", format_string)
                        if value["travel time"] <= input_travel_time:
                            result[key] = self._train_schedule[key]
                            continue
        if not result:
            return
        return result

    def delete_elements(self, del_elements: tuple | list, delete_mode: str) -> dict | None:
        """Find elements in train schedule and delete this elements.
        Return deleted elements or None."""
        elements_for_del = self.find_elements(del_elements, delete_mode)
        if not elements_for_del:
            return
        for key in list(self._train_schedule.keys())[:]:
            if key in list(elements_for_del.keys()):
                self._train_schedule.pop(key)
        return elements_for_del

    def load_schedule_xml(self, file_name: str = "trains.xml") -> dict | None:
        """Load xml save and return loaded data in dict type."""

        class TrainHandler(xml.sax.handler.ContentHandler):

            def __init__(self):
                super().__init__()
                self.__current = None
                self.__trains: dict = {}
                self.__current_id = 0
                self.__number = ""
                self.__departure_station = ""
                self.__arrival_station = ""
                self.__departure_time = ""
                self.__arrival_time = ""

            @property
            def trains(self):
                return self.__trains

            def startElement(self, name, attrs):
                self.__current = name
                if name == "train" and attrs["id"]:
                    self.__current_id = attrs["id"]
                    self.__trains[self.__current_id] = {
                        "number": "",
                        "departure station": "",
                        "arrival station": "",
                        "departure time": "",
                        "arrival time": "",
                    }

            def characters(self, content):
                if self.__current == "number":
                    self.__number = content
                if self.__current == "departure_station":
                    self.__departure_station = content
                if self.__current == "arrival_station":
                    self.__arrival_station = content
                if self.__current == "departure_time":
                    self.__departure_time = content
                if self.__current == "arrival_time":
                    if content not in [" ", "\n", "    ", "\t"]:
                        self.__arrival_time = content

            def endElement(self, name):
                format_string = "%Y-%m-%d %H:%M:%S"
                try:
                    if self.__current == "number":
                        self.__trains[self.__current_id]["number"] = self.__number
                    if self.__current == "departure_station":
                        self.__trains[self.__current_id]["departure station"] = self.__departure_station
                    if self.__current == "arrival_station":
                        self.__trains[self.__current_id]["arrival station"] = self.__arrival_station
                    if self.__current == "departure_time":
                        self.__trains[self.__current_id]["departure time"] = dt.datetime.strptime(self.__departure_time,
                                                                                                  format_string)
                    if self.__current == "arrival_time":
                        self.__trains[self.__current_id]["arrival time"] = dt.datetime.strptime(self.__arrival_time,
                                                                                                format_string)
                        self.__trains[self.__current_id]["travel time"] = \
                            self.__trains[self.__current_id]["arrival time"] - \
                            self.__trains[self.__current_id]["departure time"]
                except KeyError as err:
                    print(err)

        schedule_parse = TrainHandler()
        try:
            xml.sax.parse(file_name, schedule_parse)
        except ValueError as err:
            print(f"Unknown file: {file_name}\n{err}")
            return
        self._train_schedule = schedule_parse.trains
        self._ids = set(id for id in schedule_parse.trains.keys())
        return schedule_parse.trains

    def save_schedule_xml(self, xml_file_name: str):
        """Save dict schedule to xml file."""
        if not xml_file_name.find(".xml"):
            xml_file_name += ".xml"

        xml_save = xml.dom.minidom.Document()
        trains_group = xml_save.createElement("trains")

        for id, schedule in self._train_schedule.items():
            new_train = xml_save.createElement("train")
            new_train.setAttribute("id", id)

            number = xml_save.createElement("number")
            number.appendChild(xml_save.createTextNode(schedule["number"]))

            departure_station = xml_save.createElement("departure_station")
            departure_station.appendChild(xml_save.createTextNode(schedule["departure station"]))

            arrival_station = xml_save.createElement("arrival_station")
            arrival_station.appendChild(xml_save.createTextNode(schedule["arrival station"]))

            departure_time = xml_save.createElement("departure_time")
            departure_time.appendChild(xml_save.createTextNode(str(schedule["departure time"])))

            arrival_time = xml_save.createElement("arrival_time")
            arrival_time.appendChild(xml_save.createTextNode(str(schedule["arrival time"])))

            new_train.appendChild(number)
            new_train.appendChild(departure_station)
            new_train.appendChild(arrival_station)
            new_train.appendChild(departure_time)
            new_train.appendChild(arrival_time)

            trains_group.appendChild(new_train)

        xml_save.appendChild(trains_group)

        try:
            with open(xml_file_name, "w") as f:
                f.write(xml_save.toprettyxml())
        except OSError as err:
            print(err)
            return
