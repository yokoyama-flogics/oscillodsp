# OscilloDSP, a Virtual Oscilloscope Software for Jupyter and Embedded Processors

Copyright (c) 2020, 2021, Chubu University and Firmlogics

All rights reserved.

[Watch the demo video on YouTube.](https://www.youtube.com/watch?v=cJITVeQGVG0)

![PySide 2 app](image/pyside2_app.png)

![TI C6670 DSP EVM](image/ti_c6670_evm.jpg)

## What is OscilloDSP?

OscilloDSP is a software tool that allows users to visualize data from embedded processors, such as DSPs (Digital Signal Processors), in a way similar to an oscilloscope. It sends sensor values, computed data, or other real-time information from the embedded processor to a PC, where Python-based visualizations are generated. This is especially useful for engineers and researchers working on embedded systems, who need to analyze data from sensors or signal processing units in real-time.

## Who is it for?

This software is designed for:
- Engineers working on DSP or other embedded systems.
- Researchers in signal processing who need to visualize real-time data.
- Developers looking for an oscilloscope-like tool to monitor and analyze data directly from microcontrollers or other embedded processors.

## Motivation for Development

OscilloDSP was created to bridge the gap between embedded systems and real-time data visualization. Traditional oscilloscopes can be limited in terms of how much data they can handle and visualize from multiple sources. With OscilloDSP, users can manage large amounts of data, select the relevant information needed for visualization, and do so with a flexible Python environment. It also supports simulations for those without access to physical DSP hardware, making it versatile for both development and educational purposes.

## How does it help?

OscilloDSP reduces the communication load between an embedded processor and a PC by only sending the necessary data for visualization. It also offers flexibility in how data is visualized, with built-in support for multi-channel data display. It can be simulated on a PC without requiring DSP hardware, which is ideal for testing and development. Additionally, it leverages Google Protocol Buffers for efficient data encoding and decoding between the embedded processor and the PC.

## 日本語のドキュメント

- [インストール方法](hostapp/installation.ipynb)
- [使い方](hostapp/usage.ipynb)
- [パソコン用のオシロスコープアプリ](hostapp/oscillo.ipynb)

## Documentation in English

- [Installation Guide](hostapp/installation_en.ipynb)
- [How to Use](hostapp/usage_en.ipynb)
- [Oscilloscope app for PC](hostapp/oscillo_en.ipynb)

## License

This project is licensed under the BSD 2-Clause License.
See the [LICENSE](LICENSE) file for more details.
