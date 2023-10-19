
from pandas import Series
from scipy.stats import zscore, t

def z_score_test(s: Series, threshold: int = 2) -> list:
    """Detect the anomalies in the passed time series using the z-score test.
    The Z-score test, also known as the standard score test, is a statistical method used for anomaly detection 
    in univariate data. 
    It quantifies how far a data point is from the mean of a dataset in terms of standard deviations. 
    By comparing the Z-score of a data point to a predefined threshold, you can identify outliers or anomalies in the data. 
    

    Args:
        s (Series): Univariate time series, where index is the time stamps
        threshold (int, optional): Z-score threshold, which represented threshold * standard deviation. Defaults to 2.

    Returns:
        list: index of anomaly points
    """
    df = s.copy(deep=True).to_frame('vals')
    
    # Calculate Z-scores for the 'Value' column
    df['Z_Score'] = zscore(df['vals'])

    # Detect anomalies based on the threshold
    anomaly_indices = df[df['Z_Score'].abs() > threshold].index
    
    # Return the anomaly indices
    return anomaly_indices.to_list()


def iqr_test(s: Series):
    raise NotImplementedError("Not implemented")

def esd_test(s: Series, percentile_threshold : int = 95, alpha: float = 0.05, normalise_to: str = "median") -> list:
    """Detect the anomalies of the passed time series using the Exttreme Studentized Deviate (ESD) test.
    The ESD (Extreme Studentized Deviate) test is a statistical method used for detecting anomalies or outliers in univariate data. 
    It's particularly useful when you suspect that your data contains extreme values that are significantly different from the rest 
    of the data. The ESD test helps identify these extreme values by comparing them to a statistical distribution.

    Args:
        s (Series): Univariate time series, where index is the time stamps
        percentile_threshold (int, optional): Determine the number of ourliers to search using the number of elments that fit in the percentile_threshold. Defaults to 95.
        alpha (float, optional): P-value Significance level. Defaults to 0.05.
        normalise_to (str, optional): Use the mean or median for calculating the z-score. Median in more robust to outliers. Defaults to "median".

    Raises:
        ValueError: When the normalize factors is not ["mean", "median"]

    Returns:
        list: index of anomaly points
        
    References:
        https://bit.ly/3sR1ZxB
        https://bit.ly/3RupeIr
        
    """
    
    raise NotImplementedError("Not implemented")
    
    normalise_factors = ["mean", "median"]
    if normalise_to.lower() not in normalise_factors: 
        raise ValueError(f"Nomalisation can be one of these values {normalise_factors}")
    
    
    df = s.copy(deep=True).to_frame('vals')
    
    # Calculate the sample mean/median and standard deviation
    factor = df['vals'].mean() if normalise_to == "mean" else df['vals'].median()
    std_dev = df['vals'].std()

    # Perform the ESD test
    # max_anomalies = 5  # Maximum number of anomalies to detect
    max_anomalies_num = int(len(df['vals']) * (1 - (percentile_threshold / 100)))
    anomaly_indices = []

    for i in range(max_anomalies_num):
        # Calculate the test statistic (ESD)
        df['ESD'] = (df['vals'] - factor) / std_dev

        # Find the index of the data point with the maximum ESD
        max_esd_index = df['ESD'].abs().idxmax()

        # Get the corresponding ESD value
        max_esd_value = df.loc[max_esd_index, 'ESD']

        # Calculate the critical value for the ESD test
        n = len(df)
        alpha = alpha  # Significance level at 0.05
        critical_value = t.ppf(1 - alpha / (2 * (n - i)), n - i - 2)

        # Check if the maximum ESD value exceeds the critical value
        if abs(max_esd_value) > critical_value:
            anomaly_indices.append(max_esd_index)

        # Update mean and standard deviation after removing the identified outlier
        df = df.drop(max_esd_index)
        factor = df['vals'].mean() if normalise_to == "mean" else df['vals'].median()
        std_dev = df['vals'].std()
        
    return anomaly_indices