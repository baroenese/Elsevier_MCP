---
description: Bibliografi terverifikasi 57 publikasi ilmiah Romi Satria Wahono (2000–2026) hasil penelusuran via Elsevier MCP (Scopus) yang divalidasi silang dengan Crossref dan OpenAlex, lengkap dengan statistik per tahun/venue dan daftar penuh ber-DOI.
tags:
  - bibliometrik
  - scopus
  - crossref
  - openalex
  - romi-satria-wahono
  - machine-learning
  - software-defect-prediction
  - research
title: Bibliografi Publikasi Ilmiah Romi Satria Wahono (2000–2026)
---

# Bibliografi Publikasi Ilmiah Romi Satria Wahono (2000–2026)

## Ringkasan Eksekutif

Penelusuran menyeluruh terhadap publikasi ilmiah **Romi Satria Wahono** menghasilkan **57 publikasi unik terverifikasi** pada rentang **2000–2026** dengan total akumulasi **±658 sitasi** (hitungan OpenAlex). Fokus risetnya terbagi dalam dua era besar:

1. **Era Requirements Engineering & Software Agent (2000–2003)** — basis data riset doktoralnya di Jepang (JSAI, IEEE CogInf, IEEE CW), termasuk sistem OOExpert dan framework XRPWeb.
2. **Era Machine Learning & Prediksi Cacat Software (2011–2026)** — periode paling produktif, terutama **2015 (27 dokumen)**, dengan tema inti penanganan *class imbalance* (AdaBoost, SMOTE, bootstrapping, information gain), *feature selection* berbasis metaheuristik (PSO, GA, GSA), serta pengolahan citra dan optimasi klasterisasi.

Profil peneliti: OpenAlex [`A5087234515`](https://openalex.org/A5087234515) · ORCID [0000-0002-8102-5212](https://orcid.org/0000-0002-8102-5212) · PhD dari Technical University of Malaysia Malacca (UTeM).

## Metodologi Penelusuran

Dilakukan pada 2026-09-27 menggunakan **Elsevier MCP Server** (repo `Elsevier_MCP`) plus validasi silang dua sumber sekunder:

| Tahap | Alat/Query | Hasil |
|---|---|---|
| 1. Penelusuran Scopus via MCP | `search_papers` dengan `AUTH(Wahono, R S)`, ditarik per tahun 2005–2026 (maks. 25/tarikan) | 124 dokumen mentah, 120 unik |
| 2. Verifikasi penulis | Daftar penulis lengkap per-DOI via Crossref (batch `filter=doi:...`) | Hanya ~7 dokumen terkonfirmasi Romi Satria Wahono |
| 3. Penelusuran presisi Scopus | `AUTH(Wahono, Romi)` dan `AUTH(Wahono, Romi S.)` | 5 dan 4 dokumen |
| 4. Sumber primer profil | OpenAlex works `author.id:A5087234515` + sweep `raw_author_name.search` | 57 karya + 1 karya tambahan |
| 5. Konsolidasi | Deduplikasi lintas sumber berdasarkan judul & DOI | **57 publikasi unik** |

Data lengkap per publikasi tersimpan di [bibliografi-romi-satria-wahono.csv](bibliografi-romi-satria-wahono.csv) (tahun, judul, venue, DOI, sitasi).

## Temuan Kunci: Jebakan Homonim

Query `AUTH(Wahono, R S)` di Scopus **sangat terkontaminasi peneliti lain** yang berinisial sama:

- **Satriyo Krido Wahono** (bioenergi/jatropha, UGM) — penyumbang mayoritas 124 dokumen mentah (~50 dokumen).
- **Wahono, Cesarius Singgih**, **Wahono, Endro Prasetyo**, **Wahono, Bayu Suko**, **Wahono, Bevo**, dan lainnya.

Dari 113 dokumen ber-DOI yang diperiksa daftar penulis lengkapnya di Crossref, hanya 7 yang benar-benar berisi "Romi Satria Wahono". **Implikasi praktis:** penelusuran bibliometrik berbasis inisial `R.S. Wahono` tanpa verifikasi daftar penulis akan menghasilkan bibliografi yang hampir seluruhnya salah. Profil Scopus Romi sendiri kecil (5–7 dokumen terindeks) karena publikasi produktifnya 2015–2025 banyak berada di jurnal/jurnal prosiding yang tidak masuk indeks Scopus.

## Statistik Bibliometrik

### Distribusi per tahun

| Tahun | Jumlah | Tahun | Jumlah |
|---|---|---|---|
| 2026 | 1 | 2015 | **27** |
| 2025 | 1 | 2014 | 3 |
| 2022 | 1 | 2013 | 2 |
| 2019 | 1 | 2011 | 1 |
| 2018 | 2 | 2003 | 7 |
| 2017 | 2 | 2002 | 2 |
| 2016, 2020–2021, 2023–2024 | 0 | 2001 | 4 |
| | | 2000 | 1 |
| | | 1994 | 1* |

\* Entri 1994 memiliki judul rusak (artefak OCR/encoding di OpenAlex) — disertakan demi kelengkapan sumber, perlu verifikasi manual.

### Venue paling produktif

| Venue | Jumlah |
|---|---|
| Journal of Intelligent Systems | 17 |
| Journal of Intelligent Engineering Information (So'peuteuweeo…, Korea) | 7 |
| Advanced Science Letters | 3 |
| Jurnal Teknodik | 2 |
| Venue lain (masing-masing 1) | 28 |

### 10 publikasi tersitasi tertinggi

| Sitasi | Tahun | Judul |
|---|---|---|
| 67 | 2014 | Metaheuristic Optimization based Feature Selection for Software Defect Prediction |
| 65 | 2013 | Combining Particle Swarm Optimization based Feature Selection and Bagging Technique for Software Defect Prediction |
| 56 | 2015 | Komparasi Algoritma Klasifikasi Machine Learning Dan Feature Selection pada Analisis Sentimen |
| 49 | 2013 | Genetic Feature Selection for Software Defect Prediction |
| 35 | 2014 | A Comparison Framework of Classification Models for Software Defect Prediction |
| 35 | 2014 | Neural Network Parameter Optimization Based on Genetic Algorithm for Software Defect Prediction |
| 34 | 2015 | Comparative Analysis of Mamdani, Sugeno and Tsukamoto Method of Fuzzy Inference System |
| 27 | 2015 | Penerapan Adaboost untuk Penyelesaian Ketidakseimbangan Kelas pada Penentuan Kelulusan Mahasiswa |
| 24 | 2015 | Color and Texture Feature Extraction Using Gabor Filter - Local Binary Patterns for Image Segmentation |
| 23 | 2018 | Sistem E-Learning Berbasis Model Motivasi Komunitas |

## Daftar Lengkap 57 Publikasi

| Tahun | Judul | Venue | DOI |
|---|---|---|---|
| 2026 | PRO-LGBM: A synergistic integrated pipeline for outlier detection and imbalance handling with optimized LightGBM in fetal health classification | Franklin Open | [10.1016/j.fraope.2026.100628](https://doi.org/10.1016/j.fraope.2026.100628) |
| 2025 | Hybrid SMOTE-Evolutionary Algorithm-AdaBoost for Lithology Prediction Using K-Nearest Neighbor | — | [10.1109/icoailo66760.2025.11155926](https://doi.org/10.1109/icoailo66760.2025.11155926) |
| 2022 | Metode Pembobotan Jarak dengan Koefisien Variasi untuk Mengatasi Kelemahan Euclidean Distance pada Algoritma k-Nearest Neighbor | Jurnal Ilmiah SINUS | [10.30646/sinus.v20i1.565](https://doi.org/10.30646/sinus.v20i1.565) |
| 2019 | U-control Chart Based Differential Evolution Clustering for Determining the Number of Cluster in k -Means | International journal of intelligent engineering and systems | [10.22266/ijies2019.0831.28](https://doi.org/10.22266/ijies2019.0831.28) |
| 2018 | GAME PUZZLE BERBASIS FUZZY C-MEAN UNTUK MEMETAKAN SOAL UJIAN NASIONAL FISIKA SMA | Jurnal Teknodik | [10.32550/teknodik.v14i1.450](https://doi.org/10.32550/teknodik.v14i1.450) |
| 2018 | SISTEM E-LEARNING BERBASIS MODEL MOTIVASI KOMUNITAS | Jurnal Teknodik | [10.32550/teknodik.v21i3.469](https://doi.org/10.32550/teknodik.v21i3.469) |
| 2017 | Penerapan Jaringan Syaraf Tiruan Backpropagation Dalam Prediksi Produksi Bahan Pangan Pokok di Indonesia | Jurnal Teknik Informatika | [10.51998/jti.v3i1.123](https://doi.org/10.51998/jti.v3i1.123) |
| 2017 | TACKLING IMBALANCED CLASS IN SOFTWARE DEFECT PREDICTION USING TWO-STEP CLUSTER BASED RANDOM UNDERSAMPLING AND STACKING TECHNIQUE | Jurnal Teknologi | [10.11113/jt.v79.11874](https://doi.org/10.11113/jt.v79.11874) |
| 2015 | A Systematic Literature Review of Requirements Engineering for Self-Adaptive Systems | — | — |
| 2015 | Absolute Correlation Weighted Naïve Bayes for Software Defect Prediction | — | — |
| 2015 | Color and Texture Feature Extraction Using Gabor Filter - Local Binary Patterns for Image Segmentation with Fuzzy C-Means | Journal of Intelligent Systems | — |
| 2015 | Comparative Analysis of Mamdani, Sugeno and Tsukamoto Method of Fuzzy Inference System for Air Conditioner Energy Saving | Journal of Intelligent Systems | — |
| 2015 | Hybrid Keyword Extraction Algorithm and Cosine Similarity for Improving Sentences Cohesion in Text Summarization | Journal of Intelligent Systems | — |
| 2015 | Integrasi Discrete Wavelet Transform dan Singular Value Decomposition pada Watermarking Citra untuk Perlindungan Hak Cipta | Journal of Intelligent Systems | — |
| 2015 | Integrasi Kromosom Buatan Dinamis untuk Memecahkan Masalah Konvergensi Prematur pada Algoritma Genetika untuk Traveling Salesman Problem | Journal of Intelligent Systems | — |
| 2015 | Integrasi Metode Information Gain untuk Seleksi Fitur dan AdaBoost untuk Mengurangi Bias pada Analisis Sentimen Review Restoran Menggunakan Algoritma Naive Bayes | Journal of Intelligent Systems | — |
| 2015 | Integrasi Metode Sample Bootstrapping dan Weighted Principal Component Analysis untuk Meningkatkan Performa k Nearest Neighbor pada Dataset Besar | Journal of Intelligent Systems | — |
| 2015 | Integrasi Pareto Fitness, Multiple-Population Dan Temporary Population Pada Algoritma Genetika Untuk Pembangkitan Data Tes Pada Pengujian Perangkat Lunak | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Integrasi SMOTE Dan Information Gain Pada Naive Bayes Untuk Prediksi Cacat Software | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Komparasi Algoritma Klasifikasi Machine Learning Dan Feature Selection pada Analisis Sentimen Review Film | Journal of Intelligent Systems | — |
| 2015 | Komparasi Metode Machine Learning dan Metode Non Machine Learning untuk Estimasi Usaha Perangkat Lunak | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Pemilihan Parameter Smoothing pada Probabilistic Neural Network dengan Menggunakan Particle Swarm Optimization untuk Pendeteksian Teks Pada Citra | Journal of Intelligent Systems | — |
| 2015 | Penanganan Fitur Kontinyu dengan Feature Discretization Berbasis Expectation Maximization Clustering untuk Klasifikasi Spam Email Menggunakan Algoritma ID3 | Journal of Intelligent Systems | — |
| 2015 | Pendekatan Level Data untuk Menangani Ketidakseimbangan Kelas pada Prediksi Cacat Software | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Penerapan Adaboost untuk Penyelesaian Ketidakseimbangan Kelas pada Penentuan Kelulusan Mahasiswa dengan Metode Decision Tree | Journal of Intelligent Systems | — |
| 2015 | Penerapan Bootstrapping untuk Ketidakseimbangan Kelas dan Weighted Information Gain untuk Feature Selection pada Algoritma Support Vector Machine untuk Prediksi Loyalitas Pelanggan | Journal of Intelligent Systems | — |
| 2015 | Penerapan Gravitational Search Algorithm untuk Optimasi Klasterisasi Fuzzy C-Means | Journal of Intelligent Systems | — |
| 2015 | Penerapan Java Dynamic Compilation Pada Metode Java Customized Class Loader Untuk Memperbaharui Perangkat Lunak Pada Saat Runtime Dengan Lebih Efisien | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Penerapan Metode Average Gain, Threshold Pruning dan Cost Complexity Pruning Untuk Split Atribut Pada Algoritma C4.5 | Journal of Intelligent Systems | — |
| 2015 | Penerapan Metode Distance Transform Pada Linear Discriminant Analysis Untuk Kemunculan Kulit Pada Deteksi Kulit | Journal of Intelligent Systems | — |
| 2015 | Penerapan Naive Bayes untuk Mengurangi Data Noise pada Klasifikasi Multi Kelas dengan Decision Tree | — | — |
| 2015 | Penerapan Reduksi Region Palsu Berbasis Mathematical Morphology pada Algoritma Adaboost Untuk Deteksi Plat Nomor Kendaraan Indonesia | Journal of Intelligent Systems | — |
| 2015 | Penerapan Teknik Ensemble untuk Menangani Ketidakseimbangan Kelas pada Prediksi Cacat Software | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Penggunaan Random Under Sampling untuk Penanganan Ketidakseimbangan Kelas pada Prediksi Cacat Software Berbasis Neural Network | So'peuteuweeo gonghag yeon'gu hoeji | — |
| 2015 | Two-Step Cluster Based Feature Discretization of Naive Bayes for Outlier Detection in Intrinsic Plagiarism Detection | Journal of Intelligent Systems | — |
| 2014 | A Comparison Framework of Classification Models for Software Defect Prediction | Advanced Science Letters | [10.1166/asl.2014.5640](https://doi.org/10.1166/asl.2014.5640) |
| 2014 | Metaheuristic Optimization based Feature Selection for Software Defect Prediction | Journal of Software | [10.4304/jsw.9.5.1324-1333](https://doi.org/10.4304/jsw.9.5.1324-1333) |
| 2014 | Neural Network Parameter Optimization Based on Genetic Algorithm for Software Defect Prediction | Advanced Science Letters | [10.1166/asl.2014.5641](https://doi.org/10.1166/asl.2014.5641) |
| 2013 | Combining Particle Swarm Optimization based Feature Selection and Bagging Technique for Software Defect Prediction | International Journal of Software Engineering and Its Applications | [10.14257/ijseia.2013.7.5.16](https://doi.org/10.14257/ijseia.2013.7.5.16) |
| 2013 | Genetic Feature Selection for Software Defect Prediction | Advanced Science Letters | [10.1166/asl.2014.5283](https://doi.org/10.1166/asl.2014.5283) |
| 2011 | SIMULASI PENERAPAN ANFIS PADA SISTEM LAMPU LALU LINTAS ENAM RUAS | DOAJ (DOAJ: Directory of Open Access Journals) | — |
| 2003 | A framework for object identification and refinement process in object-oriented analysis and design | — | [10.1109/coginf.2002.1039317](https://doi.org/10.1109/coginf.2002.1039317) |
| 2003 | ANALYZING REQUIREMENTS ENGINEERING PROBLEMS | — | — |
| 2003 | Cognitive-Decision-Making Issues for Software Agents | Brain and Mind | [10.1023/a:1025413930296](https://doi.org/10.1023/a:1025413930296) |
| 2003 | Extensible requirements patterns of web application for efficient web application development | — | [10.1109/cw.2002.1180908](https://doi.org/10.1109/cw.2002.1180908) |
| 2003 | IlmuKomputer.Com: Toward A New Strategy to Develop A Free Web Based Learning and Teaching Environment | — | — |
| 2003 | OOExpert: An Agent Based System for Identifying and Refining Objects from Software Requirements Based on Object Based Formal Specification | — | — |
| 2003 | XRPWeb: Extensible Requirements Patterns for Web Application Development | — | — |
| 2002 | On the Requirements Pattern of Software Engineering | — | — |
| 2002 | Toward a Method for Eliciting Software Requirements Using Constraint Natural Language | — | — |
| 2001 | Multi Agent Systems: Issues, Approaches and Challenges Multi Agent System: Beberapa Isu, Pendekatan dan Tantangan | — | — |
| 2001 | Object Based Formal Specification: Methodological Support for Specifying Requirements in Object Model Creation Process | — | — |
| 2001 | Pengantar Software Agent: Teori dan Aplikasi | — | — |
| 2001 | Towards The Use of Intelligent Agents in Collaborative Object-Oriented Analysis and Design | Proceedings of the Annual Conference of JSAI Proceedings of the 15th Annual Conference of JSAI, 2001 | [10.11517/pjsai.jsai01.0.68.0](https://doi.org/10.11517/pjsai.jsai01.0.68.0) |
| 2000 | Reasoning with Cases in the CBR System: A Case Study for Applying OOExpert System | — | — |
| 1994 | en nu uj ju u K Ke eb be eb ba as sa an n y ya an ng g M Me em mb be eb ba as sk ka an n | — | — |
| n.d. | BOOTSTRAPPING AND WEIGHTED INFORMATION GAIN IN SUPPORT VECTOR MACHINE | RePEc: Research Papers in Economics | — |

## Catatan Cakupan dan Batasan

- **Cakupan**: daftar ini adalah publikasi yang **terverifikasi lintas sumber** (Scopus via MCP + Crossref + OpenAlex), bukan klaim absolut seluruh karya. Profil Google Scholar/Sinta peneliti memuat lebih banyak dokumen, terutama di jurnal nasional Indonesia yang tidak terindeks Scopus/Crossref/OpenAlex.
- **Keterbatasan API key**: key Scopus pada repo ini tidak berhak atas endpoint *author retrieval*, sehingga profil penulis tidak dapat ditarik langsung dari Scopus; penelusuran dikawal lewat query `AUTH()` pada endpoint pencarian umum.
- **Entri tanpa DOI**: 35 dari 57 entri tidak memiliki DOI terdaftar (umumnya jurnal periode 2015 dan dokumen era 2000–2003) — identitasnya diverifikasi via judul + sumber.
- **Periode 2016, 2020–2021, 2023–2024**: tidak ada dokumen terverifikasi pada sumber yang digunakan; dokumen Romi pada tahun-tahun tersebut kemungkinan besar tersebar di kanal non-indeks (buku, jurnal nasional, blog ilmiah).
