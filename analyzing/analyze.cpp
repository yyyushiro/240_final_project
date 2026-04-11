#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

#include <nlohmann/json.hpp>

namespace fs = std::filesystem;

using json = nlohmann::json;

/**
 * @brief Remove the dollar sign from the given string and convert it into double.
 * 
 * @param s string made by digits and a dollar sign.
 * @return double the float without dollar sign.
 */
static double parse_money(std::string s)
{
    std::size_t i = 0;
    while (i < s.size() && (s[i] == '$' || std::isspace(static_cast<unsigned char>(s[i]))))
        i++;
    return std::stod(s.substr(i));
}


/**
 * @brief load the scraping json file.
 * 
 * @return json the json object of the spending history.
 */
static json load_input_json()
{
    const char* path = "jsons/rawHistory.json";
    std::ifstream f(path);
    if (f)
        return json::parse(f);
    std::cerr << "failed to open " << path << '\n';
    std::exit(1);
}

int main()
{   
    // Load the json file and get a json object.
    const json data = load_input_json();

    // process the balances and make a new one with true float values.
    const auto& balances = data.at("balances");
    json balances_obj = json::object();
    for (const auto& row : balances)
    {
        const std::string label = row.at(0).get<std::string>();
        const double amount = parse_money(row.at(1).get<std::string>());
        if (label.find("Beginning") != std::string::npos)
            balances_obj["beginning_balance"] = amount;
        else if (label.find("Ending") != std::string::npos)
            balances_obj["ending_balance"] = amount;
    }

    // Process the timeline and make a new one with true float values.
    const auto& timeline_rows = data.at("timelineData");
    json timeline_out = json::array();
    for (const auto& row : timeline_rows)
    {
        json new_row = json::array();
        new_row.push_back(row.at(0));
        new_row.push_back(row.at(1));
        new_row.push_back(parse_money(row.at(3).get<std::string>()));
        new_row.push_back(parse_money(row.at(4).get<std::string>()));
        timeline_out.push_back(std::move(new_row));
    }

    // Create a history json object having balances and timeline.
    json history;
    history["balances"] = balances_obj;
    if (data.contains("timelineHeader"))
    {
        json header_out = json::array();
        for (const auto& h : data.at("timelineHeader"))
        {
            if (h.get<std::string>() == "Account")
                continue;
            header_out.push_back(h);
        }
        history["timelineHeader"] = std::move(header_out);
    }
    history["timelineData"] = std::move(timeline_out);

    // Format the json in a tidy way.
    const std::string history_text = history.dump(2);

    // specify the path and create a json file on it. Then, write the json object to it.
    fs::path repo_root = fs::current_path();
    const fs::path history_path = repo_root / "jsons" / "history.json";
    std::ofstream history_file(history_path);
    if (!history_file)
    {
        std::cerr << "failed to write " << history_path.string() << '\n';
        return 1;
    }
    history_file << history_text << '\n';

    return 0;
}
