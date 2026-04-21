#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <ctime>
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


static std::string parse_shop(std::string s)
{
    if (s.find("Tyler") != std::string::npos) return "Tyler";
    else if (s.find("Cellar") != std::string::npos) return "Cellar";
    else if (s.find("Passport") != std::string::npos) return "Passport";
    else if (s.find("8:15") != std::string::npos) return "8:15";
    else if (s.find("ETC") != std::string::npos) return "ETC";
    else return s;
}

/**
 * @brief Convert a "YYYY-MM-DD" string into time_t (local time, noon).
 *        Noon is used so DST shifts cannot flip the whole-day bucket.
 */
static std::time_t ymd_to_time(const std::string& s)
{
    std::tm tm{};
    tm.tm_year = std::stoi(s.substr(0, 4)) - 1900;
    tm.tm_mon  = std::stoi(s.substr(5, 2)) - 1;
    tm.tm_mday = std::stoi(s.substr(8, 2));
    tm.tm_hour = 12;
    tm.tm_isdst = -1;
    return std::mktime(&tm);
}

/**
 * @brief Whole-day difference (end - start) between two "YYYY-MM-DD" strings.
 */
static int days_between(const std::string& start, const std::string& end)
{
    const double secs = std::difftime(ymd_to_time(end), ymd_to_time(start));
    return static_cast<int>(secs / 86400.0 + (secs >= 0 ? 0.5 : -0.5));
}

/**
 * @brief Today's date in "YYYY-MM-DD" using the system clock (local time).
 */
static std::string today_ymd()
{
    const std::time_t t = std::time(nullptr);
    std::tm tm{};
#if defined(_WIN32)
    localtime_s(&tm, &t);
#else
    localtime_r(&t, &tm);
#endif
    char buf[11];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d", &tm);
    return std::string(buf);
}

/**
 * @brief Classify spending pace given the deviation-ratio and tolerance band.
 *        deviation = (ending_balance - expected_balance) / beginning_balance
 */
static std::string classify(double deviation, double tolerance)
{
    if (deviation < -tolerance) return "overspending";
    if (deviation >  tolerance) return "underspending";
    return "on_track";
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
        new_row.push_back(parse_shop(row.at(1)));
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

    // Requirement 3: classify the user's dining-dollar pace as
    // overspending / on_track / underspending based on how much of the
    // semester has elapsed versus how much balance has been used.
    const double begin_bal = balances_obj.value("beginning_balance", 0.0);
    const double end_bal   = balances_obj.value("ending_balance",   0.0);

    // Prefer dates persisted by the scraper; otherwise use the spring-semester
    // window already assumed by the visualization step.
    const std::string semester_start = data.value("fromDate", std::string("2026-01-12"));
    const std::string semester_end   = data.value("toDate",   std::string("2026-05-03"));
    const std::string today          = today_ymd();

    const int days_total   = std::max(1, days_between(semester_start, semester_end));
    const int days_elapsed = std::clamp(days_between(semester_start, today), 0, days_total);

    const double expected_balance = begin_bal * (1.0 - static_cast<double>(days_elapsed) / days_total);
    const double expected_spent   = begin_bal - expected_balance;
    const double spent            = begin_bal - end_bal;
    const double deviation        = begin_bal > 0.0 ? (end_bal - expected_balance) / begin_bal : 0.0;

    const double tolerance = 0.10;
    const std::string classification = classify(deviation, tolerance);

    const double recommended_daily_usage = end_bal / std::max(1, days_between(today, semester_end));
    const double recommended_weekly_usage = end_bal / std::max(1, days_between(today, semester_end)) * 7;

    json status;
    status["classification"]    = classification;
    status["beginning_balance"] = begin_bal;
    status["ending_balance"]    = end_bal;
    status["spent"]             = spent;
    status["expected_spent"]    = expected_spent;
    status["expected_balance"]  = expected_balance;
    status["deviation_ratio"]   = deviation;
    status["tolerance"]         = tolerance;
    status["days_elapsed"]      = days_elapsed;
    status["days_total"]        = days_total;
    status["today"]             = today;
    status["semester_start"]    = semester_start;
    status["semester_end"]      = semester_end;
    status["recommended_daily_usage"] = recommended_daily_usage;
    status["recommended_weekly_usage"] = recommended_weekly_usage;

    const fs::path status_path = repo_root / "jsons" / "status.json";
    std::ofstream status_file(status_path);
    if (!status_file)
    {
        std::cerr << "failed to write " << status_path.string() << '\n';
        return 1;
    }
    status_file << status.dump(2) << '\n';

    std::cout << "Spending status: " << classification
              << " (deviation " << deviation << ", tolerance " << tolerance << ")\n";

    return 0;
}
