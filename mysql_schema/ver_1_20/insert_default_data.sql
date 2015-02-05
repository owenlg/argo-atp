-- ----------------------------------------------------------------------------
--
-- NAME:        insert_default_data.sql
--
-- FACILITY:    SAM (Service Availability Monitoring)
--
-- COPYRIGHT:
--         Copyright (c) 2009, Members of the EGEE Collaboration.
--         http://www.eu-egee.org/partners/
--         Licensed under the Apache License, Version 2.0.
--         http://www.apache.org/licenses/LICENSE-2.0
--         This software is provided "as is", without warranties
--         or conditions of any kind, either express or implied.
--
-- DESCRIPTION:
--         Script to insert default rows in Oracle database
--
-- AUTHORS:     David Collados, CERN
--              Joshi Pradyumna, BARC
--
-- CREATED:     23-Nov-2009
--
-- NOTES:
--
-- MODIFIED: 	21-May-2011
--
-- ----------------------------------------------------------------------------

-- project
INSERT INTO project(projectname, description) VALUES ('WLCG', 'WLCG project is to build and maintain a data storage and analysis infrastructure for the entire high energy physics community that will use the Large Hadron Collider at CERN.');

-- infrastructure
INSERT INTO infrastructure(infrastname, description) VALUES ('EGI', 'A grid infrastrastructure that provides a reliable and scalable computing resource to the European and global research community');
INSERT INTO infrastructure(infrastname, description) VALUES ('OSG', 'A national distributed computing grid for data intensive research');

-- countries
INSERT INTO country(countryname, countryabbr, code) VALUES('Unknown', '', 'UN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Afghanistan', '', 'AF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Algeria', '', 'DZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('American Samoa', '', 'AS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Andorra', '', 'AD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Angola', '', 'AO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Anguilla', '', 'AI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Antarctica', '', 'AQ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Antigua and Barbuda', '', 'AG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Argentina', '', 'AR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Armenia', '', 'AM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Aruba', '', 'AW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Australia', '', 'AU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Austria', '', 'AT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Azerbaijan', '', 'AZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bahrain', '', 'BH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bangladesh', '', 'BD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Barbados', '', 'BB');
INSERT INTO country(countryname, countryabbr, code) VALUES('Belarus', '', 'BY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Belgium', '', 'BE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Belize', '', 'BZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Benin', '', 'BJ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bermuda', '', 'BM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bhutan', '', 'BT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bolivia, Plurinational State Of', 'Bolivia', 'BO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bosnia and Herzegovina', '', 'BA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Botswana', '', 'BW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bouvet Island', '', 'BV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Brazil', '', 'BR');
INSERT INTO country(countryname, countryabbr, code) VALUES('British Indian Ocean Territory', '', 'IO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Brunei Darussalam', 'Brunei', 'BN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Bulgaria', '', 'BG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Burkina Faso', '', 'BF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Burundi', '', 'BI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cameroon', '', 'CM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Canada', '', 'CA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cape Verde', '', 'CV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cayman Islands', '', 'KY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Central African Republic', '', 'CF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Chad', '', 'TD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Chile', '', 'CL');
INSERT INTO country(countryname, countryabbr, code) VALUES('China', '', 'CN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Christmas Island', '', 'CX');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cocos (Keeling) Islands', '', 'CC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Colombia', '', 'CO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Comoros', '', 'KM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Congo', '', 'CG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Congo, The Democratic Republic Of The', 'Congo, Democratic Republic', 'CD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cook Islands', '', 'CK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Costa Rica', '', 'CR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cote d''Ivoire', '', 'CI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Croatia', '', 'HR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cuba', '', 'CU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Cyprus', '', 'CY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Czech Republic', '', 'CZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Denmark', '', 'DK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Djibouti', '', 'DJ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Dominica', '', 'DM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Dominican Republic', '', 'DO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Ecuador', '', 'EC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Egypt', '', 'EG');
INSERT INTO country(countryname, countryabbr, code) VALUES('El Salvador', '', 'SV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Equatorial Guinea', '', 'GQ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Eritrea', '', 'ER');
INSERT INTO country(countryname, countryabbr, code) VALUES('Estonia', '', 'EE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Ethiopia', '', 'ET');
INSERT INTO country(countryname, countryabbr, code) VALUES('Falkland Islands (Malvinas)', 'Malvinas', 'FK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Faroe Islands', '', 'FO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Fiji', '', 'FJ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Finland', '', 'FI');
INSERT INTO country(countryname, countryabbr, code) VALUES('France', '', 'FR');
INSERT INTO country(countryname, countryabbr, code) VALUES('French Guiana', '', 'GF');
INSERT INTO country(countryname, countryabbr, code) VALUES('French Polynesia', '', 'PF');
INSERT INTO country(countryname, countryabbr, code) VALUES('French Southern Territories', '', 'TF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Gabon', '', 'GA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Gambia', '', 'GM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Georgia', '', 'GE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Germany', '', 'DE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Ghana', '', 'GH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Gibraltar', '', 'GI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Greece', '', 'GR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Greenland', '', 'GL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Grenada', '', 'GD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guadeloupe', '', 'GP');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guam', '', 'GU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guatemala', '', 'GT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guernsey', '', 'GG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guinea', '', 'GN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guinea-Bissau', '', 'GW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Guyana', '', 'GY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Haiti', '', 'HT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Heard Island and McDonald Islands', '', 'HM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Holy See (Vatican City State)', 'Vatican', 'VA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Honduras', '', 'HN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Hong Kong', '', 'HK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Hungary', '', 'HU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Iceland', '', 'IS');
INSERT INTO country(countryname, countryabbr, code) VALUES('India', '', 'IN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Indonesia', '', 'ID');
INSERT INTO country(countryname, countryabbr, code) VALUES('Iran, Islamic Republic Of', 'Iran', 'IR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Iraq', '', 'IQ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Ireland', '', 'IE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Isle of Man', 'Man', 'IM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Israel', '', 'IL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Italy', '', 'IT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Jamaica', '', 'JM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Japan', '', 'JP');
INSERT INTO country(countryname, countryabbr, code) VALUES('Jersey', '', 'JE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Jordan', '', 'JO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Kazakhstan', '', 'KZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Kenya', '', 'KE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Kiribati', '', 'KI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Korea, Democratic People''s Republic Of', 'North Korea', 'KP');
INSERT INTO country(countryname, countryabbr, code) VALUES('Korea, Republic Of', 'South Korea', 'KR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Kuwait', '', 'KW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Kyrgyzstan', '', 'KG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Lao People''s Democratic Republic', 'Laos', 'LA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Latvia', '', 'LV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Lebanon', '', 'LB');
INSERT INTO country(countryname, countryabbr, code) VALUES('Lesotho', '', 'LS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Liberia', '', 'LR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Libyan Arab Jamahiriya', 'Libya', 'LY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Liechtenstein', '', 'LI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Lithuania', '', 'LT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Luxembourg', '', 'LU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Macao', 'Macau', 'MO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Macedonia', 'FYROM', 'MK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Madagascar', '', 'MG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Malawi', '', 'MW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Malaysia', '', 'MY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Maldives', '', 'MV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mali', '', 'ML');
INSERT INTO country(countryname, countryabbr, code) VALUES('Malta', '', 'MT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Marshall Islands', '', 'MH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Martinique', '', 'MQ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mauritania', '', 'MR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mauritius', '', 'MU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mayotte', '', 'YT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mexico', '', 'MX');
INSERT INTO country(countryname, countryabbr, code) VALUES('Micronesia, Federated States of', '', 'FM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Moldova, Republic of', 'Moldova', 'MD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Monaco', '', 'MC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mongolia', '', 'MN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Montenegro', '', 'ME');
INSERT INTO country(countryname, countryabbr, code) VALUES('Montserrat', '', 'MS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Morocco', '', 'MA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Mozambique', '', 'MZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Myanmar', '', 'MM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Namibia', '', 'NA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Nauru', '', 'NR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Nepal', '', 'NP');
INSERT INTO country(countryname, countryabbr, code) VALUES('Netherlands', '', 'NL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Netherlands Antilles', '', 'AN');
INSERT INTO country(countryname, countryabbr, code) VALUES('New Caledonia', '', 'NC');
INSERT INTO country(countryname, countryabbr, code) VALUES('New Zealand', '', 'NZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Nicaragua', '', 'NI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Niger', '', 'NE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Nigeria', '', 'NG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Niue', '', 'NU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Norfolk Island', '', 'NF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Northern Mariana Islands', '', 'MP');
INSERT INTO country(countryname, countryabbr, code) VALUES('Norway', '', 'NO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Oman', '', 'OM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Pakistan', '', 'PK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Palau', '', 'PW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Palestinian Territory, Occupied', '', 'PS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Panama', '', 'PA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Papua New Guinea', '', 'PG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Paraguay', '', 'PY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Peru', '', 'PE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Philippines', '', 'PH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Pitcairn', 'Pitcairn Islands', 'PN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Poland', '', 'PL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Portugal', '', 'PT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Puerto Rico', '', 'PR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Qatar', '', 'QA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Reunion', '', 'RE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Romania', '', 'RO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Russian Federation', 'Russia', 'RU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Rwanda', '', 'RW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Barthelemy', '', 'BL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Helena', '', 'SH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Kitts and Nevis', '', 'KN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Lucia', '', 'LC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Martin', '', 'MF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Pierre and Miquelon', '', 'PM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saint Vincent and the Grenadines', '', 'VC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Samoa', '', 'WS');
INSERT INTO country(countryname, countryabbr, code) VALUES('San Marino', '', 'SM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Sao Tome and Principe', '', 'ST');
INSERT INTO country(countryname, countryabbr, code) VALUES('Saudi Arabia', '', 'SA');
INSERT INTO country(countryname, countryabbr, code) VALUES('Senegal', '', 'SN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Serbia', '', 'RS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Seychelles', '', 'SC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Sierra Leone', '', 'SL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Singapore', '', 'SG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Slovakia', '', 'SK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Slovenia', '', 'SI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Solomon Islands', '', 'SB');
INSERT INTO country(countryname, countryabbr, code) VALUES('Somalia', '', 'SO');
INSERT INTO country(countryname, countryabbr, code) VALUES('South Africa', '', 'ZA');
INSERT INTO country(countryname, countryabbr, code) VALUES('South Georgia and the South Sandwich Islands', '', 'GS');
INSERT INTO country(countryname, countryabbr, code) VALUES('Spain', '', 'ES');
INSERT INTO country(countryname, countryabbr, code) VALUES('Sri Lanka', '', 'LK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Sudan', '', 'SD');
INSERT INTO country(countryname, countryabbr, code) VALUES('Suriname', '', 'SR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Svalbard and Jan Mayen', 'Svalbard', 'SJ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Swaziland', '', 'SZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Sweden', '', 'SE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Switzerland', '', 'CH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Syrian Arab Republic', 'Syria', 'SY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Taiwan, Province of China', 'Taiwan', 'TW');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tajikistan', '', 'TJ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tanzania, United Republic of', 'Tanzania', 'TZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Thailand', '', 'TH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Timor-Leste', 'Timor', 'TL');
INSERT INTO country(countryname, countryabbr, code) VALUES('Togo', '', 'TG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tokelau', '', 'TK');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tonga', '', 'TO');
INSERT INTO country(countryname, countryabbr, code) VALUES('Trinidad and Tobago', '', 'TT');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tunisia', '', 'TN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Turkey', '', 'TR');
INSERT INTO country(countryname, countryabbr, code) VALUES('Turkmenistan', '', 'TM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Turks and Caicos Islands', '', 'TC');
INSERT INTO country(countryname, countryabbr, code) VALUES('Tuvalu', '', 'TV');
INSERT INTO country(countryname, countryabbr, code) VALUES('Uganda', '', 'UG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Ukraine', '', 'UA');
INSERT INTO country(countryname, countryabbr, code) VALUES('United Arab Emirates', '', 'AE');
INSERT INTO country(countryname, countryabbr, code) VALUES('United Kingdom', 'UK', 'GB');
INSERT INTO country(countryname, countryabbr, code) VALUES('United States', 'USA', 'US');
INSERT INTO country(countryname, countryabbr, code) VALUES('United States Minor Outlying Islands', '', 'UM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Uruguay', '', 'UY');
INSERT INTO country(countryname, countryabbr, code) VALUES('Uzbekistan', '', 'UZ');
INSERT INTO country(countryname, countryabbr, code) VALUES('Vanuatu', '', 'VU');
INSERT INTO country(countryname, countryabbr, code) VALUES('Venezuela, Bolivarian Republic of', 'Venezuela', 'VE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Vietnam', '', 'VN');
INSERT INTO country(countryname, countryabbr, code) VALUES('Virgin Islands, British', '', 'VG');
INSERT INTO country(countryname, countryabbr, code) VALUES('Virgin Islands, U.S.', '', 'VI');
INSERT INTO country(countryname, countryabbr, code) VALUES('Wallis and Futuna', '', 'WF');
INSERT INTO country(countryname, countryabbr, code) VALUES('Western Sahara', '', 'EH');
INSERT INTO country(countryname, countryabbr, code) VALUES('Yemen', '', 'YE');
INSERT INTO country(countryname, countryabbr, code) VALUES('Zambia', '', 'ZM');
INSERT INTO country(countryname, countryabbr, code) VALUES('Zimbabwe', '', 'ZW');

-- Non GOCDB service flavours
INSERT INTO service_type_flavour(flavourname) VALUES ('OSG-BestmanXrootd');
INSERT INTO service_type_flavour(flavourname) VALUES ('OSG-CE');
INSERT INTO service_type_flavour(flavourname) VALUES ('OSG-GridFtp');
INSERT INTO service_type_flavour(flavourname) VALUES ('OSG-SRMv2');
INSERT INTO service_type_flavour(flavourname) VALUES ('SRMv2');
INSERT INTO service_type_flavour(flavourname) VALUES ('MPICH');
INSERT INTO service_type_flavour(flavourname) VALUES ('MPICH2');
INSERT INTO service_type_flavour(flavourname) VALUES ('OPENMPI');

-- Synchronizers
INSERT INTO synchronizer(name, updateminutes) VALUES ('CIC', 30);
INSERT INTO synchronizer(name, updateminutes) VALUES ('GOCDB', 30);
INSERT INTO synchronizer(name, updateminutes) VALUES ('GSTAT', 30);
INSERT INTO synchronizer(name, updateminutes) VALUES ('OIM', 30);
INSERT INTO synchronizer(name, updateminutes) VALUES ('BDII', 30);
INSERT INTO synchronizer(name, updateminutes) VALUES ('VO-Feeds',30);

-- OPS VO
INSERT INTO group_type(typename, description) VALUES('Site', 'Group of physical sites for OPS VO');
INSERT INTO group_type(typename, description) VALUES('Region', 'Group of sites in a region for OPS VO');
INSERT INTO group_type(typename, description) VALUES('Tier', 'Group of sites in a Tier for OPS VO');
INSERT INTO group_type(typename, description) VALUES('Federation', 'Group of sites in a Federation for OPS VO');

-- ATLAS VO
INSERT INTO group_type(typename, description) VALUES('ATLAS_Site', 'Group of sites for ATLAS VO');
INSERT INTO group_type(typename, description) VALUES('ATLAS_Cloud', 'Group of sites in a cloud for ATLAS VO');
INSERT INTO group_type(typename, description) VALUES('ATLAS_Tier', 'Group of sites in a Tier for ATLAS VO');
INSERT INTO group_type(typename, description) VALUES('ATLAS_Group', 'Group of sites in a group for ATLAS VO');

-- CMS VO
INSERT INTO group_type(typename, description) VALUES('CMS_Site', 'Group of sites for CMS VO');
INSERT INTO group_type(typename, description) VALUES('CMS_Cloud', 'Group of sites in a cloud for CMS VO');
INSERT INTO group_type(typename, description) VALUES('CMS_Tier', 'Group of sites in a Tier for CMS VO');
INSERT INTO group_type(typename, description) VALUES('CMS_Group', 'Group of sites in a group for CMS VO');

-- LHCb VO
INSERT INTO group_type(typename, description) VALUES('LHCb_Site', 'Group of sites for LHCb VO');
INSERT INTO group_type(typename, description) VALUES('LHCb_Cloud', 'Group of sites in a cloud for LHCb VO');
INSERT INTO group_type(typename, description) VALUES('LHCb_Tier', 'Group of sites in a Tier for LHCb VO');
INSERT INTO group_type(typename, description) VALUES('LHCb_Group', 'Group of sites in a group for LHCb VO');

-- ALICE VO
INSERT INTO group_type(typename, description) VALUES('ALICE_Site', 'Group of sites for ALICE VO');
INSERT INTO group_type(typename, description) VALUES('ALICE_Cloud', 'Group of sites in a cloud for ALICE VO');
INSERT INTO group_type(typename, description) VALUES('ALICE_Tier', 'Group of sites in a Tier for ALICE VO');
INSERT INTO group_type(typename, description) VALUES('ALICE_Group', 'Group of sites in a group for ALICE VO');


-- Groups
CALL GROUPS_INSERT('Region', 'Unknown', 'Sites not registered under any region');
CALL GROUPS_INSERT('Region', 'OSG', 'Sites under OSG');
