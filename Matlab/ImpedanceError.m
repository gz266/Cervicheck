% Data table
data = [ ...
   -0.0303030303  -9.216666667  -45.54727273  -49.53617021  -50.28928571; 
   36.39393939     0            -16.52727273  -21.81276596  -22.98035714;
   51.51515152     3.675         0.6484848485 -18.45106383  -21.91607143;
   99.18181818    51.925        17.95151515    5.774468085   4.523214286;
   246.3030303    45.35         12.84545455    4.182978723   1.0625];

rowLabels = [330 1200 3300 5600 8300];
colLabels = [330 1200 3300 4700 5600];

% Initialize color matrix
colors = zeros([size(data), 3]);

% Assign colors based on conditions
for i = 1:size(data,1)
    for j = 1:size(data,2)
        val = abs(data(i,j));
        if val < 10
            colors(i,j,:) = [0, 1, 0];      % green
        elseif val < 40
            colors(i,j,:) = [1, 1, 0];      % yellow
        else
            colors(i,j,:) = [1, 0.6, 0.6];  % lighter red
        end
    end
end

% Plot using imagesc
figure;
imagesc(data); % use the data grid as placeholder
hold on;

% Overlay colored patches
for i = 1:size(data,1)
    for j = 1:size(data,2)
        rectangle('Position',[j-0.5, i-0.5, 1, 1], ...
                  'FaceColor', squeeze(colors(i,j,:)), ...
                  'EdgeColor','k');
        % Add text value (larger font size, bold, darker color)
        text(j, i, sprintf('%.1f', data(i,j)), ...
            'HorizontalAlignment','center', ...
            'VerticalAlignment','middle', ...
            'FontSize',14,'FontWeight','bold','Color','k');
    end
end

% Adjust axes
set(gca,'XTick',1:length(colLabels),'XTickLabel',colLabels, ...
        'YTick',1:length(rowLabels),'YTickLabel',rowLabels, ...
        'FontSize',12,'FontWeight','bold');
xlabel('Columns'); ylabel('Rows');
title('Percent Error Color Map','FontSize',16,'FontWeight','bold');
axis equal tight;

%% 5600 - 12000

% Data table
data = [ ...
     0            5.227352941   -6.603780488  -13.6239      -20.62816667; 
     1.502857143  0            -10.05317073  -15.7095      -19.86125;
    12.84785714   3.342058824    0            -6.2885      -13.88766667;
    12.37375     15.59779412     1.068902439   0            -8.109083333;
    23.37196429  18.63014706    16.12743902   12.3466        0];

rowLabels = [5600 6800 8200 10000 12000];
colLabels = [5600 6800 8200 10000 12000];

% Initialize color matrix
colors = zeros([size(data), 3]);

% Assign colors based on conditions
for i = 1:size(data,1)
    for j = 1:size(data,2)
        val = abs(data(i,j));
        if val < 10
            colors(i,j,:) = [0, 1, 0];      % green
        elseif val < 40
            colors(i,j,:) = [1, 1, 0];      % yellow
        else
            colors(i,j,:) = [1, 0.6, 0.6];  % lighter red
        end
    end
end

% Plot using imagesc
figure;
imagesc(data); % use the data grid as placeholder
hold on;

% Overlay colored patches
for i = 1:size(data,1)
    for j = 1:size(data,2)
        rectangle('Position',[j-0.5, i-0.5, 1, 1], ...
                  'FaceColor', squeeze(colors(i,j,:)), ...
                  'EdgeColor','k');
        % Add text value (larger font size, bold, darker color)
        text(j, i, sprintf('%.2f', data(i,j)), ...
            'HorizontalAlignment','center', ...
            'VerticalAlignment','middle', ...
            'FontSize',14,'FontWeight','bold','Color','k');
    end
end

% Adjust axes
set(gca,'XTick',1:length(colLabels),'XTickLabel',colLabels, ...
        'YTick',1:length(rowLabels),'YTickLabel',rowLabels, ...
        'FontSize',12,'FontWeight','bold');
xlabel('Columns'); ylabel('Rows');
title('Percent Error Color Map','FontSize',16,'FontWeight','bold');
axis equal tight;

%% 5600 - 12000

% Data table
data = [ ...
     0            -17.53786667  -28.45322222  -36.44045455  -46.0097037;
    16.05958333    0            -10.56655556  -20.55054545  -32.51211111;
    34.096        15.54066667    3.332055556   -8.203545455 -22.02407407;
    52.25008333   31.18266667   13.53805556    4.223909091  -11.46759259;
    71.971        34.73706667   28.24466667   17.72404545    0];


rowLabels = [12000 15000 18000 22000 27000]; 
colLabels = [12000 15000 18000 22000 27000];

% Initialize color matrix
colors = zeros([size(data), 3]);

% Assign colors based on conditions
for i = 1:size(data,1)
    for j = 1:size(data,2)
        val = abs(data(i,j));
        if val < 10
            colors(i,j,:) = [0, 1, 0];      % green
        elseif val < 40
            colors(i,j,:) = [1, 1, 0];      % yellow
        else
            colors(i,j,:) = [1, 0.6, 0.6];  % lighter red
        end
    end
end

% Plot using imagesc
figure;
imagesc(data); % use the data grid as placeholder
hold on;

% Overlay colored patches
for i = 1:size(data,1)
    for j = 1:size(data,2)
        rectangle('Position',[j-0.5, i-0.5, 1, 1], ...
                  'FaceColor', squeeze(colors(i,j,:)), ...
                  'EdgeColor','k');
        % Add text value (larger font size, bold, darker color)
        text(j, i, sprintf('%.2f', data(i,j)), ...
            'HorizontalAlignment','center', ...
            'VerticalAlignment','middle', ...
            'FontSize',14,'FontWeight','bold','Color','k');
    end
end

% Adjust axes
set(gca,'XTick',1:length(colLabels),'XTickLabel',colLabels, ...
        'YTick',1:length(rowLabels),'YTickLabel',rowLabels, ...
        'FontSize',12,'FontWeight','bold');
xlabel('Columns'); ylabel('Rows');
title('Percent Error Color Map','FontSize',16,'FontWeight','bold');
axis equal tight;
