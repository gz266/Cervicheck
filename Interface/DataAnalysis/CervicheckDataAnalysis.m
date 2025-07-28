%% Data Analysis Script
% Use 3 functions to
% (1) Obtain a and C values
% (2) Plot stress strain curves
% (3) Plot bar graph to compare different materials


function [alpha_coeff, C_coeff, eff_modulus, mean_modulus, std_modulus] = analyze(fit_type, stretch, varargin)
%{
Returns: None
Parameters: arrays of stress values to be analyzed. Arrays can be of
different sizes
- takes each stress array, finds a fit value
- trims down the stretch array as needed to match sizes
- Adds 0 starting point to input stress arrays
%}
alpha_coeff = zeros(size(varargin));
C_coeff = zeros(size(varargin));
eff_modulus = zeros(size(varargin));
    for t = 1:max(size(varargin))
        % Process Stretch and Strain Arrays
        cur_stress = [0 varargin{t}]*-1;
        if max(size(cur_stress)) ~= max(size(stretch))
            cur_stretch = stretch(1:max(size(cur_stress)));
        else
            cur_stretch = stretch;
        end
        % Perform Curve Fitting
        fit_values = fit(cur_stretch' ,cur_stress',fit_type, 'StartPoint', [1, 1]);
        coeff = coeffvalues(fit_values);
        alpha_coeff(t) = coeff(1);
        C_coeff(t) = coeff(2);
        eff_modulus(t) = alpha_coeff(t)*C_coeff(t)*(-0.052*(alpha_coeff(t)^3)+0.252*(alpha_coeff(t)^2)+(0.053*alpha_coeff(t))+1.09);
    end
    mean_modulus = mean(eff_modulus);
    std_modulus = std(eff_modulus);
end

function [] = plot_all(a, C, stretch, varargin)
%{
Returns: None
Parameters: derived alpha and C values from the analyze function
- stretch 
%}
    for t = 1:max(size(varargin))
        % Process Stretch and Strain Arrays
        cur_stress = [0 varargin{t}]*-1;
        if max(size(cur_stress)) ~= max(size(stretch))
            cur_stretch = stretch(1:max(size(cur_stress)));
        else
            cur_stretch = stretch;
        end
        plot(cur_stretch, cur_stress, '.', 'MarkerSize', 12, 'Color', '#808080');
        x = stretch(1) : 0.001 : stretch(max(size(cur_stress)));
        y = a(t).*C(t).*((x.^2)-(1./x)).*exp(a(t).*((x.^2)+(2./x)-3));
        plot(x,y, '-b');
    end
end

function [] = plot_youngs(legend, varargin)
%{
Returns: None
Parameters: array of modulus after analyzing data, plots bar graph with different 
arrays of modulus
- legend: labels of array
%}
    for t = 1:max(size(varargin))
        mean_modulus = mean(varargin{t});
        std_modulus = std(varargin{t});
        bar(t-1, mean_modulus);
        
        % Plot Error Bars
        er = errorbar(t-1,mean_modulus,std_modulus,std_modulus);    
        er.Color = [0 0 0];                            
        er.LineStyle = 'none';
        
        % Plot Individual Values
        x_values = ones(size(varargin{t}))*(t-1);
        plot(x_values, varargin{t}, '.', 'MarkerSize', 15, 'Color', '#808080');
    end
    curtick = get(gca, 'xTick');
    xticks(unique(round(curtick)));
    % Set x bounds
    ax = gca;
    ax.XLim = [-0.5, max(size(varargin))-0.5];
    set(gca,'xticklabel', legend);
end

%% Example Workflow
% Raw Data 

cauchy = fittype("a*C*((x^2)-(1/x))*exp(a*((x^2)+(2/x)-3))",dependent="y",independent="x",coefficients=["a" "C"]);

% Stretch is dependent on the geometry of the flex PCB
stretch = [1 1.2415 1.406 1.572 1.738 1.9045 2.071 2.2375];

% Process 1% Agarose Data
s1 = [-1.34 -7.32];
s2 = [-1 -2.35 -2.99 -3.96 -5.01 -9.31 -10.02];
s3 = [-1.34 -2.01 -3.36 -5.31 -12.24];
s4 = [-0.97 -2.01 -3.36 -10.02 -15.97];
s5 = [-1.27 -2.01 -3.02 -4.37 -10.05 -19.28];
s6 = [-1.1 -2.28 -3.02 -4.06 -5.27 -10.02 -18.26];
s7 = [-1.27 -2.01 -3.36 -4 -5.01 -7.06];
s8 = [-1.27 -1.98 -3.36 -4 -5.01 -6.05 -15.03];
s9 = [-1.27 -3.32 -6.38 -15.03];
s10 = [-1.14 -2.08 -3.32 -7.36 -19.26];
s11 = [-1.31 -2.01 -6.01 -9.94 -14.22 -20];
s12 = [-3.29 -5.27 -13.98 -15.99];
s13 = [-3.02 -4.29 -9.97 -13.2 -20.17];
s14 = [-3.02 -4.26 -10.95 -13.98];
s15 = [-6.01 -7.05 -16 -20.24];

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10);

figure;
hold on
plot_all(a1, c1, stretch, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("1% Agarose Stress Strain Curves: 7/15/2025");
hold off

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, s11, s12, s13, s14, s15);

figure;
hold on
plot_all(a1, c1, stretch, s11, s12, s13, s14, s15);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("1% Agarose Stress Strain Curves: 7/16/2025");
hold off

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15);
disp(a1);
disp(c1);
disp(e1);

figure;
hold on
plot_all(a1, c1, stretch, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("1% Agarose Stress Strain Curves: All");
hold off

% Process 2% Agarose Data
t1 = [-1.07 -13.18];
t2 = [-7.93 -9.98 -19.03];
t3 = [-1.34 -7.33 -14.02];
t4 = [-1.07 -2.99 -6.01 -19.16];
t5 = [-1.31 -2.01 -8.03 -22.16];
t6 = [-1 -6.01 -22.16];
t7 = [-1.1 -2.01 -3.32 -14.02];
t8 = [-0.97 -4.27 -10.02 -21.01];
t9 = [-1.1 -2.28 -14.29];
t10 = [-1 -2.32 -5.27 -12];
t11 = [-6.01 -7.05 -16 -20.24];
t12 = [-3.15 -4.03 -10.95 -19];
t13 = [-1.2 -4.97 -23.13];
t14 = [-3.96 -8.03];
t15 = [-2.95 -6.05];

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10);

figure;
hold on
plot_all(a1, c1, stretch, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("2% Agarose Stress Strain Curves: 7/15/2025");
hold off

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, t11, t12, t13, t14, t15);

figure;
hold on
plot_all(a1, c1, stretch, t11, t12, t13, t14, t15);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("2% Agarose Stress Strain Curves: 7/16/2025");
hold off

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15);
disp(a1);
disp(c1);
disp(e1);

figure;
hold on
plot_all(a1, c1, stretch, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("2% Agarose Stress Strain Curves: All");
hold off

% Process 7.5% Polyacrylamide Data
u1 = [-1.34 -2.04 -3.05 -8.03];
u2 = [-7.05 -8.33];
u3 = [-3.02 -8.29 -14.99];
u4 = [-3.15 -13.03 -19.97];
u5 = [-1.17 -2.08 -7.06 -12.94 -19];
u6 = [-4.4 -11.06 -19.26 -25.32];
u7 = [-1.24 -12.07 -23.97];
u8 = [-5.17 -8.46 -17.48 -25.25];
u9 = [-6.65 -18.56 -25.59];
u10 = [-8.44 -10.12 -22.32];
u11 = [-1.14 -8.37 -19.1];
u12 = [-2.52 -4.4 -12.03 -17.21 -23.06 -28.04];
u13 = [-3.56 -4.2 -13.48 -17.38 -23.37 -27.34];
u14 = [-10.05 -15.06 -27.27];
u15 = [-1.21 -2.21 -10.22 -15.16 -21.99 -28.01];

[a1, c1, e1, e_avg, e_std] = analyze(cauchy, stretch, u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14, u15);
disp(a1);
disp(c1);
disp(e1);

figure;
hold on
plot_all(a1, c1, stretch, u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14, u15);

xlabel("Strain");
ylabel("Stress (kPa)");
fontsize(20, "points");
title("7.5% Polyacrylamide Stress Strain Curves: 7/16/2025");
hold off
