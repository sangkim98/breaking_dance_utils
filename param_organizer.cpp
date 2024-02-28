#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>

using namespace std;
using json = nlohmann::json;

int main(int argc, char* argv[]){
    
    ifstream fin;
    ofstream fout;

    if(argc != 3){
        cout << argc << " number of arguments not supported" << endl;

        return 1;
    }

    fin.open(argv[1], ifstream::in);

    if(!fin){
        cout << argv[1] << " not found" << endl;
        fin.close();

        return 2;
    }

    fout.open(argv[2], ofstream::out);

    if(!fout){
        cout << argv[2] << " not created" << endl;
        fout.close();

        return 2;        
    }

    string line;

    json data = json::parse(fin);

    cout << fixed;
    cout.precision(20);

    for(auto& elem : data["cam0"]["dist"]){
        // cout << elem;
        printf("%.20lf ", double(elem));
    }

    return 0;
}